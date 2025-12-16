from typing import Iterable, Tuple
import posixpath
from mbctl.MBConfig import mb_config
from mbctl.datatypes import MBContainerMountConf, MBContainerMountPointConf
from dataclasses import dataclass

from mbctl.datatypes.MountType import MountType


def get_mount_point_src(container_name: str, mount_type: MountType, inner_path: str = "/") -> str:
    inner = inner_path.lstrip("/")
    base_dir = posixpath.join(mb_config.storage_path, mount_type.value, container_name)
    return posixpath.join(base_dir, inner)


# 虽然这里有默认值，但在创建的时候必须都指定出来。
@dataclass
class MBContainerMountEntry:
    # owner、perm指的是source路径的权限设置。
    owner: list[int]  # [0, 0]  # [uid, gid]
    perm: str  # "755"/"644"
    source: str  # host path
    target: str  # container path
    file: bool  # whether it's a file mount point
    type: MountType  # mount type

    def to_docker_mount_str(self) -> str:
        return f"{self.source}:{self.target}"


# 一个容器所有的挂载相关的功能都在这里实现。
class MBContainerMount:

    def __init__(self, container_name: str, mount_conf: MBContainerMountConf):
        self.container_name = container_name
        # host, inner
        self.mount_points: list[MBContainerMountEntry] = self._build_mount_points(
            mount_conf
        )

    def _build_mount_points(
        self, mount_conf: MBContainerMountConf
    ) -> list[MBContainerMountEntry]:
        mount_points: list[MBContainerMountEntry] = []
        mount_map = {
            MountType.data: mount_conf.data,
            MountType.log: mount_conf.log,
            MountType.conf: mount_conf.conf,
            MountType.cache: mount_conf.cache,
            MountType.plugin: mount_conf.plugin,
        }
        for mount_type, mounts in mount_map.items():
            for inner_path, conf in mounts.items():
                host_path = get_mount_point_src(self.container_name, mount_type, inner_path)
                mount_points.append(
                    MBContainerMountEntry(
                        owner=conf.owner,
                        perm=conf.perm, # type: ignore
                        source=host_path,
                        target=inner_path,
                        file=conf.file,
                        type=mount_type,
                    )
                )
        return mount_points

    def to_compose_volumes(self) -> list[str]:
        return [entry.to_docker_mount_str() for entry in self.mount_points]

    def to_mbcontainer_mount_conf(self) -> MBContainerMountConf:
        mount_conf = MBContainerMountConf()
        mount_map = {
            MountType.data: mount_conf.data,
            MountType.log: mount_conf.log,
            MountType.conf: mount_conf.conf,
            MountType.cache: mount_conf.cache,
            MountType.plugin: mount_conf.plugin,
        }
        for entry in self.mount_points:
            mount_map[entry.type][entry.target] = MBContainerMountPointConf(
                owner=entry.owner,
                perm=entry.perm,
                source=entry.source,
            )
        return mount_conf
