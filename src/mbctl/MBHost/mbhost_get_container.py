from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import MBHost
from typing import Optional
from mbctl.datatypes import MBContainerConf
from mbctl.datatypes import MountType
from mbctl.MBConfig import mb_config
from mbctl.MBContainer import MBContainer, MBContainerMount, MBContainerStatus
from .NerdClient import NerdClient, NerdContainerState
import os


# 这里的所有函数，都不检查 container_name 的合法性，调用者必须保证传入的 container_name 对应着真正的MBContainer。
def get_container_status(self: MBHost, container_name: str) -> MBContainerStatus:
    """获得容器当前状态。"""
    nerd_container_state = self.client.get_container_state(container_name)

    if nerd_container_state == NerdContainerState.not_exist:
        return MBContainerStatus.never
    elif nerd_container_state == NerdContainerState.running:
        return MBContainerStatus.running
    elif nerd_container_state == NerdContainerState.stopped:
        return MBContainerStatus.stopped
    else:
        return MBContainerStatus.unknown


def get_mbcontainer_conf(self: MBHost, container_name: str) -> MBContainerConf:
    """根据缓存或配置文件获得一个MBContainerConf对象。"""
    self._ensure_container_loaded(container_name)
    container_conf_path = self.get_container_conffile_path(container_name)
    return MBContainerConf.from_yaml_file(container_conf_path)


def get_mbcontainer(self: MBHost, container_name: str) -> MBContainer:
    """根据配置文件获得一个MBContainer对象。"""
    self._ensure_container_loaded(container_name)
    target_container = self._containers_by_name.get(container_name)
    if target_container is None:
        raise KeyError(f"Container '{container_name}' not found.")
    return target_container
