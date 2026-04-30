# 更新远程配置文件中的
import os

from mbctl.datatypes import MountType
from mbctl.datatypes.MBContainerConfFormat import update_mbcontainer_autostart
from mbctl.MBConfig import mb_config
from posixpath import join


def update_mbcontainer_autostart_config(container_name: str, autostart: bool) -> None:
    """Update container autostart config in disk file while preserving format.
    
    Uses RoundTrip YAML to preserve comments and formatting.
    
    Args:
        container_name: Name of the container
        autostart: New autostart value
    """
    config_base_dir = join(mb_config.storage_path, MountType.conf.value)
    container_conf_path = join(config_base_dir, container_name, mb_config.config_file)
    update_mbcontainer_autostart(container_conf_path, autostart)
