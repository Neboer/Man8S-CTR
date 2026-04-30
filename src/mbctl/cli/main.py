from typing import Annotated
import typer
from mbctl.NerdClient.NerdClient import NerdClient
from mbctl.NerdClient.NerdContainerInfo import (
    NerdContainerInfo,
)
from mbctl.MBHost.Loader import load_all_mbcontainers
from mbctl.MBContainer import MBContainer
from mbctl.MBLog import mb_logger
from sys import argv

from mbctl.cli.update_mbcontainer import (
    autostart_mbcontainers,
    set_mbcontainer_autostart,
)
from mbctl.datatypes import MBContainerConf

from .HostingMBContainer import HostingMBContainer, get_hosting_mbcontainers_list
from .print_hostingmbcontainers import (
    print_full_hosting_mbcontainers,
    print_short_hosting_mbcontainers,
)
from .be_shell import online_shell, network_shell
from .build_mb_container import build_mbcontainer
from mbctl.MBConfig import mb_config
from mbctl.network.address import get_ipv6_addr_prefix

import copy as copy_module
import os

__version__ = "v0.8.3"

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
    containers, _ = load_all_mbcontainers(get_ipv6_addr_prefix(mb_config.yggaddr))
    mb_logger.debug(f"Loaded {len(containers)} MBContainer configurations.")
    return containers


def get_running_container_infos() -> list[NerdContainerInfo]:
    """获取当前正在运行的容器信息列表。"""
    infos = client.list_all_containers()
    mb_logger.debug(f"Found {len(infos)} running containers.")
    return infos


# 一种性能不是很好的实现，无所谓了，不差这点性能。
def get_container_info_by_name(name: str) -> NerdContainerInfo | None:
    """根据容器名称获取容器信息，如果没有找到则返回 None。"""
    infos = get_running_container_infos()
    for info in infos:
        if info.names == name:
            return info
    return None


# mbctl run xxx --pull
@app.command(
    "run",
    help="Stop & RM (if exists) and Build & start a Man8S-managed container by name.",
)
def run_command(
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
    containers = load_compose_configs()
    container = containers[container_name]
    build_mbcontainer(
        container=container,
        container_name=container_name,
        client=client,
        pull=pull,
        detach=detach,
    )


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


@app.command(
    "enable",
    help="Enable autostart for a container.",
)
def enable_autostart(
    container_name: Annotated[
        str, typer.Argument(help="Target container nameto enable autostart.")
    ],
    now: Annotated[
        bool,
        typer.Option(
            "--now",
            help="Immediately start the container after enabling autostart.",
        ),
    ] = False,
):
    containers = load_compose_configs()
    container = containers[container_name]
    container_info = get_container_info_by_name(container.name)

    set_mbcontainer_autostart(
        nerd_client=client,
        container=container,
        container_name=container_name,
        container_info=container_info,
        autostart=True,
        now=now,
    )


@app.command(
    "disable",
    help="Disable autostart for a container.",
)
def disable_autostart(
    container_name: Annotated[
        str, typer.Argument(help="Target container name to disable autostart.")
    ],
    now: Annotated[
        bool,
        typer.Option(
            "--now",
            help="Immediately stop the container after disabling autostart.",
        ),
    ] = False,
):
    containers = load_compose_configs()
    container = containers[container_name]
    container_info = get_container_info_by_name(container.name)

    set_mbcontainer_autostart(
        nerd_client=client,
        container=container,
        container_name=container_name,
        container_info=container_info,
        autostart=False,
        now=now,
    )


@app.command(
    "autostart",
    help="Start all autostart-enabled containers in dependency order.",
)
def autostart_command():
    _, container_tree = load_all_mbcontainers(
        get_ipv6_addr_prefix(mb_config.yggaddr)
    )
    container_infos = get_running_container_infos()
    autostart_mbcontainers(client, container_tree, container_infos)


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
        cli_args = copy_module.copy(argv)
        cli_args[0] = "nerdctl"
        just_like_nerdctl(cli_args)  # just like nerdctl's execution.


if __name__ == "__main__":
    main()
