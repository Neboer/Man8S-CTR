from __future__ import annotations

import os
from posixpath import join
from typing import TYPE_CHECKING

from mbctl.MBContainer import MBContainer, MBContainerTree
from mbctl.datatypes import MBContainerConf, MountType

from mbctl.MBConfig import mb_config


def load_all_mbcontainers(
    yggdrasil_prefix: str,
) -> tuple[dict[str, MBContainer], MBContainerTree]:
    """Load all MBContainers from disk and return an MBContainerTree."""
    config_base_dir = join(mb_config.storage_path, MountType.conf.value)
    container_names = [
        name
        for name in os.listdir(config_base_dir)
        if os.path.isdir(join(config_base_dir, name))
    ]
    containers = []
    for container_name in container_names:
        container_conf_path = join(
            config_base_dir, container_name, mb_config.config_file
        )
        container_conf = MBContainerConf.from_yaml_file(container_conf_path)
        containers.append(MBContainer(container_name, container_conf, yggdrasil_prefix))
    container_tree = MBContainerTree(containers)
    container_tree.resolve_all()

    return {container.name: container for container in containers}, container_tree


def load_mbcontainer_config_by_name(container_name: str) -> MBContainerConf:
    config_base_dir = join(mb_config.storage_path, MountType.conf.value)
    container_conf_path = join(config_base_dir, container_name, mb_config.config_file)
    return MBContainerConf.from_yaml_file(container_conf_path)
