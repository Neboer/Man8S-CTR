from typing import Annotated
import typer
from mbctl.MBHost import MBHost
from prettytable import PrettyTable, TableStyle
from mbctl.MBContainer import MBContainer
from mbctl.datatypes import MBContainerConf, MBContainerMetadataConf
from sys import argv
import copy

__version__ = "v0.2"

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
    ]
):
    print(f"Building container: {container_name}")
    host.build_new_container(container_name)


@app.command("prune", help="Remove mounts and cached data for a container.")
def prune_mbcontainer(
    container_name: Annotated[
        str, typer.Argument(help="Target container name to prune mounts for.")
    ]
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
    ]
):
    print(f"preparing container: {container_name}")
    container_conf = MBContainerConf(
        image=image
    )
    host.create_container_from_conf(container_name, container_conf)


@app.command(
    "rerun",
    help="Recreate a container by forcing deletion and rebuilding it from its source image.",
)
def rebuild_mbcontainer(
    container_name: Annotated[
        str, typer.Argument(help="Container name to rebuild from scratch.")
    ],
    update: Annotated[
        bool, typer.Option("--update", "-u", help="Pull the latest image before recreating.")
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

# execute command just like nerdctl's executing.
def just_like_nerdctl(commands):
    host.client.execute_any_command(commands)


def main():
    command_names = [c.name for c in app.registered_commands]
    global_flags = {"--help", "-h", "--version", "-v"}
    if len(argv) == 1 or argv[1] in command_names or any(
        flag in argv[1:] for flag in global_flags
    ):
        app(prog_name="mbctl")
    else:
        cli_args = copy.copy(argv)
        cli_args[0] = "nerdctl"
        just_like_nerdctl(cli_args) # just like nerdctl's execution.
    
if __name__ == "__main__":
    main()
