from typing import Optional, cast, Literal

from mbctl.MBContainer import MBContainer, MBContainerTree
from mbctl.NerdClient import NerdClient
from mbctl.MBHost.UpdateConfig import write_mbcontainer_config
from mbctl.MBHost.Loader import load_all_mbcontainers, load_mbcontainer_config_by_name
from mbctl.NerdClient.NerdContainerInfo import (
    NerdContainerInfo,
    NerdContainerStatusKind,
)
from mbctl.cli.build_mb_container import build_mbcontainer
from mbctl.datatypes import MBContainerConf
from mbctl.MBLog import mb_logger


def _write_autostart_config_if_needed(
    container: MBContainer, autostart: bool
) -> bool:
    """更新磁盘配置并同步内存中的 autostart 值。"""
    if container.autostart == autostart:
        return False

    container_conf: MBContainerConf = load_mbcontainer_config_by_name(container.name)
    container_conf.autostart = autostart
    write_mbcontainer_config(container.name, container_conf)
    container.autostart = autostart
    return True


def _restart_policy_for_autostart(autostart: bool) -> str:
    return "unless-stopped" if autostart else "no"


def autostart_mbcontainers(
    nerd_client: NerdClient,
    container_tree: MBContainerTree,
    container_infos: list[NerdContainerInfo],
) -> None:
    """按依赖顺序启动所有配置了 autostart 的、且当前对应 nerdctl 容器存在的容器。"""
    info_by_name = {info.names: info for info in container_infos}

    for level in container_tree.levels():
        for container in sorted(level, key=lambda c: c.name):
            if not container.autostart:
                continue

            container_info = info_by_name.get(container.name)
            if container_info is None or container_info.status_info is None:
                mb_logger.warning(
                    f"NerdContainer {container.name} has no corresponding runtime container, skipping autostart."
                )
                continue

            status_kind = container_info.status_info.kind
            if status_kind == NerdContainerStatusKind.up:
                continue
            if status_kind == NerdContainerStatusKind.restarting:
                mb_logger.warning(
                    f"NerdContainer {container.name} is restarting, skipping autostart."
                )
                continue

            mb_logger.info(f"Starting autostart container {container.name}.")
            nerd_client.start_container(container.name)


def set_mbcontainer_autostart(
    nerd_client: NerdClient,
    container: MBContainer,
    container_name: str,
    container_info: Optional[NerdContainerInfo],
    autostart: bool = True,
    now: bool = False,
) -> None:
    """启用或禁用容器的 autostart，并可选立即启动/停止运行时容器。"""
    config_changed = _write_autostart_config_if_needed(container, autostart)
    desired_restart_policy = _restart_policy_for_autostart(autostart)

    if container_info is None or container_info.status_info is None:
        if now and autostart:
            mb_logger.info(
                f"NerdContainer {container.name} has no runtime container, creating and starting it now."
            )
            build_mbcontainer(
                container=container,
                container_name=container_name,
                client=nerd_client,
                pull=False,
                detach=True,
            )
        elif now and not autostart:
            mb_logger.info(
                f"NerdContainer {container.name} has no runtime container, nothing to stop."
            )
        return

    status_kind = container_info.status_info.kind

    if status_kind == NerdContainerStatusKind.created:
        # Created 状态下不尝试用 update 修改 restart policy（containerd 无 task 会失败）。
        # 仅写入配置；如果用户指定 --now 且希望启用 autostart，则立刻启动该容器。
        if config_changed:
            mb_logger.info(
                f"NerdContainer {container.name} updated autostart config on disk (container in 'created' state)."
            )
        if now and autostart:
            mb_logger.info(f"Starting NerdContainer {container.name} immediately from 'created' state.")
            nerd_client.start_container(container.name)
        return

    if config_changed:
        nerd_client.update_container_restart_policy(
            container.name,
            cast(Literal["no", "always", "on-failure", "unless-stopped"], desired_restart_policy),
        )
        mb_logger.info(
            f"NerdContainer {container.name} restart policy updated to {desired_restart_policy}."
        )

    if not now:
        return

    if autostart:
        if status_kind == NerdContainerStatusKind.up:
            mb_logger.info(f"NerdContainer {container.name} is already running.")
        elif status_kind == NerdContainerStatusKind.restarting:
            mb_logger.warning(
                f"NerdContainer {container.name} is restarting, skipping immediate start."
            )
        else:
            mb_logger.info(f"Starting NerdContainer {container.name} immediately.")
            nerd_client.start_container(container.name)
    else:
        if status_kind in (
            NerdContainerStatusKind.up,
            NerdContainerStatusKind.restarting,
        ):
            mb_logger.info(f"Stopping NerdContainer {container.name} immediately.")
            nerd_client.stop_and_wait_container_safely(container.name, hide=True)
