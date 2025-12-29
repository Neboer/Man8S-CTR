from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import MBHost
from mbctl.MBContainer import MBContainer, MBContainerMount, MBContainerMountEntry
from mbctl.datatypes import MBContainerConf

import os

def create_container_from_conf(
    self: MBHost, container_name: str, container_conf: MBContainerConf
) -> None:
    """Prepare a new container, create its mbconfig file onto the host."""
    container_conf_path = self.get_container_conffile_path(container_name)
    # realize the path's parent directory
    os.makedirs(os.path.dirname(container_conf_path), exist_ok=True)
    container_conf.to_yaml_file(container_conf_path)
    # reload cache to include the new container and keep references resolved
    self._reload_and_resolve_containers()


# 将一个MBContainer配置第一次运行起来成为一个container，是程序的主要功能。
def build_new_container(self: MBHost, container_name: str) -> None:
    # 1. 读取容器配置
    container = self.get_mbcontainer(container_name)

    # 2. 创建挂载目录
    for mount_entry in container.mount.mount_points:
        prepare_mount_entry(mount_entry)
    # 3. 使用nerdctl创建容器
    self.client.compose_create_container(container.to_compose_conf())

def build_all_containers(self: MBHost) -> None:
    """Build all containers defined in the MBHost's container tree."""
    for container in self._container_tree.bfs_traversal():
        self.build_new_container(container.name)

def realize_dir_mount_conf(
    mount_dir: str, uid: int = 0, gid: int = 0, perm: str = "755"
) -> None:
    """Create mount directory with specified owner and permission."""

    os.makedirs(mount_dir, exist_ok=True)
    os.chown(mount_dir, uid, gid)
    os.chmod(mount_dir, int(perm, 8))


# 对一个挂载点进行准备工作（创建目录或检查文件存在性）
def prepare_mount_entry(mount_entry: MBContainerMountEntry) -> None:
    if not mount_entry.file:  # 只创建目录挂载点，跳过文件挂载点。
        # 为什么要跳过？因为自动创建文件挂载点甚至只是创建它的父目录都会引起极大的困惑。
        realize_dir_mount_conf(
            mount_entry.source.real_mount_source_path,
            mount_entry.owner[0],
            mount_entry.owner[1],
            mount_entry.perm,
        )
    else:
        # 如果是文件挂载点，则检查此挂载点的实际源文件是否存在，如果不存在则报错并不要创建。
        if not os.path.exists(mount_entry.source.real_mount_source_path):
            raise FileNotFoundError(
                f"Mount source file {mount_entry.source} does not exist."
            )
        elif not os.path.isfile(mount_entry.source.real_mount_source_path):
            raise FileNotFoundError(f"Mount source {mount_entry.source} is not a file.")
