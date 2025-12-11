from pathlib import Path
from typing import Dict
from mbctl.datatypes import (
    MBContainerConf,
    ComposeConf,
    MBContainerMountConf,
    MBContainerMountPointConf,
)
from msgspec import json, yaml, structs
from mbctl.MBConfig import mb_config
from os import path


def to_mount_source(container_name: str, mount_type: str, inner_path: str) -> str:
    return path.join(mb_config.storage_path, mount_type, inner_path[1:])


# Convert MBContainerMountConf to Docker Compose volume strings
def convert_mount_to_info(
    mbcontainer_mount_conf: MBContainerMountConf,  # some_container
    container_name: str,
) -> list[tuple[str, str]]:
    volume_strings: list[tuple[str, str]] = []

    mount_types: Dict[str, Dict[str, MBContainerMountPointConf]] = {
        "datadir": mbcontainer_mount_conf.datadir,
        "logdir": mbcontainer_mount_conf.logdir,
        "confdir": mbcontainer_mount_conf.confdir,
        "cachedir": mbcontainer_mount_conf.cachedir,
        "plugindir": mbcontainer_mount_conf.plugindir,
    }  # pyright: ignore[reportAssignmentType]

    for mount_type, mounts in mount_types.items():
        for inner_path, mount_conf in mounts.items():
            host_path = to_mount_source(container_name, mount_type, inner_path)
            volume_strings.append((host_path, inner_path))

    return volume_strings
