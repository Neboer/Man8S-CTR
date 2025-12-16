from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import MBHost
from mbctl.MBContainer import MBContainer
from prettytable import PrettyTable, TableStyle
import os

def list_all_mbcontainer_names(self: MBHost) -> list[str]:
    """List all container names on this host."""
    return [
        name
        for name in os.listdir(self.config_base_dir)
        if os.path.isdir(os.path.join(self.config_base_dir, name))
    ]

def list_containers(self: MBHost) -> list[MBContainer]:
    """List all containers on this host."""
        # 列出所有的容器，并整理他们的状态，打印他们的名字、镜像、运行状态以及ygg地址。
    all_container_names = self.list_all_mbcontainer_names()
    return [self.get_mbcontainer(name) for name in all_container_names]
