from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import MBHost
from typing import Optional
import os
from mbctl.MBContainer.MBContainerStatus import MBContainerStatus
from mbctl.datatypes.MountType import MountType
from .NerdClient.NerdClient import NerdClient
from mbctl.MBContainer.MBContainerMount import (
    MBContainerMountEntry,
    get_mount_point_src,
)
from shutil import rmtree


def remove_container_mounts(
    self: MBHost,
    container_name: str,
    target_mount_type: Optional[list[MountType]] = None,
) -> None:
    """Remove mount directories of specified types for a container."""
    if target_mount_type is None:
        # 默认删除所有类型的挂载点
        target_mount_type = [
            MountType.data,
            MountType.log,
            MountType.conf,
            MountType.cache,
            MountType.plugin,
            MountType.socket
        ]

    target_container = self.get_mbcontainer(container_name)
    if target_container.status == MBContainerStatus.running:
        raise RuntimeError(
            f"Cannot remove mount points for running container '{container_name}'. Please stop it first."
        )
    else:
        for mount_entry in target_container.mount.mount_points:
            if mount_entry.type in target_mount_type:
                if not mount_entry.file:
                    if os.path.exists(mount_entry.source.real_mount_source_path):
                        rmtree(mount_entry.source.real_mount_source_path)
                else:
                    os.remove(mount_entry.source.real_mount_source_path)
