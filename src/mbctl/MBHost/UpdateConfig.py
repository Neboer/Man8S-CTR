# 更新远程配置文件中的
import os

from mbctl.datatypes import MBContainerConf, MountType
from mbctl.MBConfig import mb_config
from posixpath import join


def write_mbcontainer_config(container_name: str, new_conf: MBContainerConf):
    # 更新硬盘中保存的容器配置文件，如果容器不存在，会创建新的配置文件。
    config_base_dir = join(mb_config.storage_path, MountType.conf.value)

    container_conf_path = join(config_base_dir, container_name, mb_config.config_file)
    if not os.path.exists(container_conf_path):
        os.makedirs(os.path.dirname(container_conf_path), exist_ok=True)

    new_conf.to_yaml_file(container_conf_path)
