from typing import Annotated
import typer
from mbctl.NerdClient.NerdClient import NerdClient
from mbctl.NerdClient.NerdContainerInfo import NerdContainerInfo
from mbctl.MBHost.LoadMBContainers import load_mbcontainer_config
from mbctl.MBHost.MakeMountdirs import prepare_mount_entry
from mbctl.MBContainer import MBContainer
from mbctl.MBLog import mb_logger
from sys import argv

from .HostingMBContainer import HostingMBContainer, get_hosting_mbcontainers_list
from .print_hostingmbcontainers import (
    print_full_hosting_mbcontainers,
    print_short_hosting_mbcontainers,
)
from .be_shell import online_shell, network_shell
from mbctl.MBConfig import mb_config
from mbctl.network.address import get_ipv6_addr_prefix

import copy
import os

__version__ = "v0.7.0-alpha.1"

app = typer.Typer(
    help=(
        "mbctl is a Man8S container orchestration tool built on nerdctl/containerd. "
        "It delivers core Man8S workflows such as building or recreating containers, "
        "managing autostart policy, and wiring Yggdrasil networking. When a command "
        "is not recognized, mbctl proxies to nerdctl so you can keep using familiar "
        "container maintenance commands."
    )
)


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


client = NerdClient()  # 这个client一定是本机，其实这个client的设计非常多余。


def load_compose_configs() -> dict[str, MBContainer]:
    """加载所有的 MBContainer 配置文件，返回 MBContainerTree 对象。"""
    mb_logger.debug("Loading MBContainer configurations...")
    containers, _ = load_mbcontainer_config(get_ipv6_addr_prefix(mb_config.yggaddr))
    mb_logger.debug(f"Loaded {len(containers)} MBContainer configurations.")
    return containers


def get_running_container_infos() -> list[NerdContainerInfo]:
    """获取当前正在运行的容器信息列表。"""
    infos = client.list_all_containers()
    mb_logger.debug(f"Found {len(infos)} running containers.")
    return infos


# mbctl run xxx --pull
@app.command(
    "run",
    help="Stop & RM (if exists) and Build & start a Man8S-managed container by name.",
)
def build_mbcontainer(
    container_name: Annotated[
        str, typer.Argument(help="Container name defined in Man8S compose-style specs.")
    ],
    pull: Annotated[
        bool,
        typer.Option("--pull", "-p", help="Pull the latest image before recreating."),
    ] = False,
    detach: Annotated[
        bool,
        typer.Option("--detach", "-d", help="Don't show log output, just run."),
    ] = False,
):
    print(f"Running container: {container_name}")
    containers = load_compose_configs()
    for e in containers[container_name].mount.entries:
        prepare_mount_entry(e)
    client.stop_and_wait_container_safely(container_name)
    client.remove_container(container_name, safe=True)
    client.compose_create_container(
        container_name,
        containers[container_name].to_compose_conf().to_compose_dict(),
        pull=pull,
    )
    if not detach:
        client.next_command_will_execvp()
        client.monitor_container_logs(container_name)


# mbctl list
@app.command("list", help="List all managed containers and their runtime details.")
def list_all_mbcontainers(
    long: Annotated[
        bool,
        typer.Option(
            "--long", "-l", help="Show detailed information of each container."
        ),
    ] = False,
):
    containers = load_compose_configs()
    infos = get_running_container_infos()
    hosting_mbcontainers = get_hosting_mbcontainers_list(containers, infos)

    if long:
        print_full_hosting_mbcontainers(hosting_mbcontainers)
    else:
        print_short_hosting_mbcontainers(hosting_mbcontainers)


@app.command(
    "shell",
    help="Execute commands just like nerdctl's executing, default to bash shell.",
)
def nerdctl_shell(
    container_name: Annotated[
        str,
        typer.Argument(help="Target container name to execute commands in."),
    ],
    network: Annotated[
        bool,
        typer.Option(
            "--network", "-n", help="Only enter the network namespace of the container."
        ),
    ] = False,
):
    if network:
        containers = load_compose_configs()
        c = containers[container_name]
        network_shell(client, c)
    else:
        online_shell(client, container_name)


# 就像nerdctl一样执行命令，这里直接使用 os.execvp 来替换当前进程。
def just_like_nerdctl(commands: list[str]) -> None:
    # mb_logger.debug(f"Proxying command to nerdctl: {' '.join(commands)}")
    client.next_command_will_execvp()
    client.execute(commands, safe=False)


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
        just_like_nerdctl(cli_args)  # just like nerdctl's execution.


if __name__ == "__main__":
    main()
