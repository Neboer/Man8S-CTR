from typing import Annotated
import typer
from mbctl.MBHost import MBHost
from prettytable import PrettyTable, TableStyle
from mbctl.MBContainer import MBContainer, MBContainerStatus
from mbctl.datatypes import MBContainerConf, MBContainerMetadataConf
from mbctl.MBLog import mb_logger
from sys import argv
import copy

__version__ = "v0.5"

app = typer.Typer(
    help=(
        "mbctl is a Man8S container orchestration tool built on nerdctl/containerd. "
        "It delivers core Man8S workflows such as building or recreating containers, "
        "managing autostart policy, and wiring Yggdrasil networking. When a command "
        "is not recognized, mbctl proxies to nerdctl so you can keep using familiar "
        "container maintenance commands."
    )
)
host = MBHost()


def _version_callback(value: bool):
    if value:
        typer.echo(f"mbctl {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            is_eager=True,
            callback=_version_callback,
            help="Show mbctl version and exit.",
        ),
    ] = False,
):
    """Entrypoint for global options such as --version."""
    return version


@app.command("run", help="Build and start a Man8S-managed container by name.")
def build_mbcontainer(
    container_name: Annotated[
        str, typer.Argument(help="Container name defined in Man8S compose-style specs.")
    ],
):
    print(f"Building container: {container_name}")
    host.build_new_container(container_name)


@app.command("prune", help="Remove mounts and cached data for a container.")
def prune_mbcontainer(
    container_name: Annotated[
        str, typer.Argument(help="Target container name to prune mounts for.")
    ],
):
    print(f"Pruning container: {container_name}")
    host.remove_container_mounts(container_name)


@app.command(
    "create",
    help="Create a new container from an image with optional Yggdrasil and autostart settings.",
)
def create_new_mbcontainer(
    container_name: Annotated[
        str,
        typer.Argument(help="Container name to register under Man8S management."),
    ],
    image: Annotated[
        str,
        typer.Option(
            prompt="Please input a image.",
            help="Container image reference, for example: library/redis:latest.",
        ),
    ],
):
    print(f"preparing container: {container_name}")
    container_conf = MBContainerConf(image=image)
    host.create_container_from_conf(container_name, container_conf)


@app.command(
    "rerun",
    help="Recreate a container by forcing deletion and rebuilding it from its source image.",
)
def rebuild_mbcontainer(
    container_name: Annotated[
        str, typer.Argument(help="Container name to rebuild from scratch.")
    ],
    pull: Annotated[
        bool,
        typer.Option("--pull", "-p", help="Pull the latest image before recreating."),
    ] = False,
):
    print(f"Recreating container: {container_name}")
    host.client.force_delete_container(container_name)
    host.build_new_container(container_name)


@app.command("autostart", help="Start every container marked with autostart.")
def start_all_autostart_mbcontainers():
    containers = host.list_containers()
    for container in containers:
        if container.autostart:
            print(f"Starting container: {container.name}")
            host.client.start_container(container.name)


@app.command("list", help="List all managed containers and their runtime details.")
def list_all_mbcontainers():
    table = PrettyTable()
    table.field_names = ["Container", "Image", "Status", "AutoStart", "YggAddr"]

    table.add_rows(
        [
            [
                container.name,
                container.image,
                container.status.value,
                "Yes" if container.autostart else "No",
                container.yggdrasil_addr,
            ]
            for container in host.list_containers()
        ]
    )
    table.set_style(TableStyle.PLAIN_COLUMNS)
    table.align = "l"
    # table.padding_width = 1
    print(table)


@app.command(
    "shell",
    help="Execute commands just like nerdctl's executing, default to bash shell.",
)
def nerdctl_shell(
    container_name: Annotated[
        str,
        typer.Argument(help="Target container name to execute commands in."),
    ],
):
    shell_command = [
        "sh",
        "-c",
        "if [ -x /bin/bash ]; then exec /bin/bash; else exec /bin/sh; fi",
    ]

    if host.get_container_status(container_name) == MBContainerStatus.running:
        rc = host.client.execute_any_command_safely(
            ["nerdctl", "exec", "-it", container_name] + shell_command
        )
        raise typer.Exit(code=rc if rc is not None else -2)
    else:
        # 离线模式：以代替模式启动一个配置等同，但交互运行
        # 离线模式的原理是，启动一个临时的容器，采用和原容器一样的dhcp hostname，这样确保ygg地址和原容器一致，但命令行改为交互式shell。
        # 至于resolve reference，
        print(
            f"Container '{container_name}' is not running. Starting a temporary shell container..."
        )
        # 首先需要retag原容器，防止新容器与原容器冲突。
        host.client.rename_container(
            container_name, f"{container_name}_mbctl_offline_temp"
        )
        # 然后创建一个临时容器，配置和原容器一样，但是命令行改为交互式shell。
        container = host.get_mbcontainer(container_name)
        container.extra_compose_configs.update(
            {
                "tty": True,
                "stdin_open": True,
                "entrypoint": shell_command,
            }
        )
        # 程序会阻塞在此，直到用户退出shell。
        exit_code = host.client.compose_create_container_safe(
            container.to_compose_conf()
        )
        # 确保容器退出
        host.client.stop_and_wait_container(f"{container_name}_mbctl_offline_temp")
        # 最后删除与原容器名字相同的临时容器，并将原容器名改回来。
        print("Cleaning up temporary shell container...")
        host.client.force_delete_container(f"{container_name}")
        host.client.rename_container(
            f"{container_name}_mbctl_offline_temp", container_name
        )
        print("Cleanup complete.")
        raise typer.Exit(code=exit_code)


@app.command(
    "netshell",
    help="Execute commands just like nerdctl's executing, default to bash shell.",
)
def nerdctl_netshell(
    container_name: Annotated[
        str,
        typer.Argument(help="Target container name to execute commands in."),
    ],
):
    # 只进入容器的网络名字空间，使用nsenter命令，不进入容器的挂载点。
    if host.get_container_status(container_name) == MBContainerStatus.running:
        pid = host.client.get_container_pid(container_name)
        nsenter_command = [
            "nsenter",
            "-t",
            str(pid),
            "-n",
            "bash",
        ]
        print(f"Entering network namespace of container '{container_name}' (PID: {pid})...")
        rc = host.client.execute_any_command_safely(nsenter_command)
        print(f"Exited network namespace of container '{container_name}'.")
        raise typer.Exit(code=rc if rc is not None else -2)
    else:
        print(f"Container '{container_name}' is not running. Cannot enter network namespace.")
        raise typer.Exit(code=-2)

# execute command just like nerdctl's executing.
def just_like_nerdctl(commands):
    return host.client.execute_any_command_safely(commands)


def main():
    command_names = [c.name for c in app.registered_commands]
    global_flags = {"--help", "-h", "--version", "-v"}
    if (
        len(argv) == 1
        or argv[1] in command_names
        or any(flag in argv[1:] for flag in global_flags)
    ):
        app(prog_name="mbctl")
    else:
        cli_args = copy.copy(argv)
        cli_args[0] = "nerdctl"
        rc = just_like_nerdctl(cli_args)  # just like nerdctl's execution.
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
