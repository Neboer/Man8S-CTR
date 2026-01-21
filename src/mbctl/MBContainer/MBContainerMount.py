from typing import Iterable, Mapping, Optional, Sequence, Tuple
import posixpath
from mbctl.MBConfig import mb_config
from mbctl.MBContainer import MBContainer
from mbctl.datatypes import (
    MBContainerMountConf,
    MBContainerMountPointConf,
    MBContainerConf,
)
from dataclasses import dataclass

from mbctl.datatypes.MountType import MountType


def get_mount_point_src(
    container_name: str, mount_type: MountType, inner_path: str = "/"
) -> str:
    inner = inner_path.lstrip("/")
    base_dir = posixpath.join(mb_config.storage_path, mount_type.value, container_name)
    return posixpath.join(base_dir, inner)


# mount source可能是引用，为了保持配置文件的一致性，我们定义一个专门的数据结构来表示这种可以引用的source的取值。
@dataclass
class MBContainerMountEntrySource:
    is_reference: bool  # 是否是引用其他容器的挂载点
    referenced_container_name: Optional[str] = None  # 被引用的容器名称
    referenced_inner_path: Optional[str] = None  # 被引用的容器内路径

    # 真实的挂载点路径。当挂载地址不是引用时，直接复制配置中的source或默认路径；当挂载地址是引用时，此值为解析出被引用容器的真实路径。
    # 也就是说，当挂载地址是引用时，只有在引用被正确解析之后此值才会被正确的设置，在此之前这个值是空的。
    real_mount_source: Optional[str] = None

    @property
    def real_mount_source_path(self) -> str:
        if self.real_mount_source is None:
            raise ValueError("real_mount_source is not set yet.")
        else:
            return self.real_mount_source

    def to_mbconfig_mount_source_str(self) -> str:
        if self.is_reference:
            return f"{self.referenced_container_name}:{self.referenced_inner_path}"
        else:
            return self.real_mount_source  # type: ignore


# MBContainerMountEntry是已经解析过了的最终版本的挂载点配置，里面不允许出现 container_name:/data 这种形式的路径。
@dataclass
class MBContainerMountEntry:
    # owner、perm指的是source路径的权限设置。
    owner: list[int]  # [0, 0]  # [uid, gid]
    perm: str  # "755"/"644"
    source: MBContainerMountEntrySource  # host path
    target: str  # container path
    file: bool  # whether it's a file mount point
    type: MountType  # mount type

    def to_docker_mount_str(self) -> str:
        return f"{self.source.real_mount_source}:{self.target}"


# 一个容器所有的挂载相关的功能都在这里实现。
class MBContainerMount:

    def __init__(
        self,
        container_name: str,
        mount_conf: MBContainerMountConf,
    ):
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
            MountType.socket: mount_conf.socket
        }
        for mount_type, mounts in mount_map.items():
            for inner_path, conf in mounts.items():
                host_default_path = get_mount_point_src(
                    self.container_name, mount_type, inner_path
                )

                # 计算容器的挂载源：
                # - 若 source 为 "<container>:<inner_path>" 形式，则标记为引用，真实路径留待 resolve 阶段解析。
                # - 否则使用显式的 source 或者默认的宿主路径。
                if conf.source is not None and isinstance(conf.source, str):
                    if ":" in conf.source:
                        ref_container_name, ref_inner_path = conf.source.split(":", 1)
                        entry_source = MBContainerMountEntrySource(
                            is_reference=True,
                            referenced_container_name=ref_container_name,
                            referenced_inner_path=ref_inner_path,
                            real_mount_source=None,
                        )
                    else:
                        entry_source = MBContainerMountEntrySource(
                            is_reference=False,
                            real_mount_source=conf.source,
                        )
                else:
                    entry_source = MBContainerMountEntrySource(
                        is_reference=False,
                        real_mount_source=host_default_path,
                    )

                mount_points.append(
                    MBContainerMountEntry(
                        owner=conf.owner,
                        perm=conf.perm,  # type: ignore
                        source=entry_source,
                        target=inner_path,
                        file=conf.file,
                        type=mount_type,
                    )
                )
        return mount_points

    def resolve_references(self, reference_containers: Mapping[str, MBContainer]) -> None:
        for entry in self.mount_points:
            if entry.source.is_reference:
                if (
                    entry.source.referenced_container_name is None
                    or entry.source.referenced_inner_path is None
                ):
                    raise ValueError("Invalid reference mount source configuration.")

                ref_container = self._get_referenced_container(
                    entry.source.referenced_container_name,
                    reference_containers,
                )

                ref_mount_entry = ref_container.mount.get_mount_entry_by_target(
                    entry.source.referenced_inner_path
                )
                # 设置真实的挂载路径
                entry.source.real_mount_source = (
                    ref_mount_entry.source.real_mount_source
                )
                # 如果是reference，那么其他属性保持与被引用的项目一致
                entry.owner = ref_mount_entry.owner
                entry.perm = ref_mount_entry.perm
                entry.file = ref_mount_entry.file

    def _get_referenced_container(
        self, ref_container_name: str, reference_containers: Mapping[str, MBContainer]
    ) -> MBContainer:
        ref_container = reference_containers.get(ref_container_name)
        if ref_container is None:
            raise ValueError(
                f"Referenced container '{ref_container_name}' not found for mount source."
            )
        return ref_container

    def get_mount_entry_by_target(self, target_path: str) -> MBContainerMountEntry:
        entry = next((e for e in self.mount_points if e.target == target_path), None)
        if entry is None:
            raise ValueError(
                f"Mount entry with target path '{target_path}' not found in container '{self.container_name}'."
            )
        return entry

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
                source=entry.source.to_mbconfig_mount_source_str(),
                file=entry.file,
            )
        return mount_conf
