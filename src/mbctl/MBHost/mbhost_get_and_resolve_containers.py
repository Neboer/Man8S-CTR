from __future__ import annotations

import os
from posixpath import join
from typing import TYPE_CHECKING

from mbctl.MBContainer import MBContainer, MBContainerTree
from mbctl.datatypes import MBContainerConf

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from . import MBHost


# 从磁盘读取一个容器配置并构造 MBContainer
def _load_container_from_disk(self: MBHost, container_name: str) -> MBContainer:
    container_conf = MBContainerConf.from_yaml_file(
        self.get_container_conffile_path(container_name)
    )
    container_status = self.get_container_status(container_name)
    return MBContainer(container_name, container_conf, self.yggprefix, container_status)


# 发现磁盘上的容器名称
def _discover_container_names(self: MBHost) -> list[str]:
    return [
        name
        for name in os.listdir(self.config_base_dir)
        if os.path.isdir(join(self.config_base_dir, name))
    ]


# 重新加载并解析所有容器
def _reload_and_resolve_containers(self: MBHost) -> None:
    containers = [
        _load_container_from_disk(self, name) for name in _discover_container_names(self)
    ]
    if containers:
        MBContainerTree(containers).resolve_all()
    self._containers_by_name = {c.name: c for c in containers}


# 确保缓存包含指定容器（用于延迟加载新增容器）
def _ensure_container_loaded(self: MBHost, container_name: str) -> None:
    if container_name not in self._containers_by_name:
        _reload_and_resolve_containers(self)
