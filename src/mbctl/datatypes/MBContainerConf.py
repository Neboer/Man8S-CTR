from typing import Optional, Tuple
from msgspec import Struct, field
from datetime import datetime
from os import path
from mbctl.MBConfig import mb_config


def is_valid_path(p: str) -> bool:
    # Simple validation to check if the path is absolute and does not contain illegal characters
    return p.startswith("/") and ".." not in p


class MBContainerMountPointConf(Struct, omit_defaults=True):
    owner: list[int] = field(default_factory=lambda: [0, 0])  # [uid, gid]
    perm: str = field(default="755")
    source: Optional[str] = None  # source path

    def __post_init__(self):
        if self.source and not is_valid_path(self.source):
            raise ValueError(f"Invalid source path: {self.source}")


class MBContainerMountConf(Struct, omit_defaults=True):
    datadir: Optional[dict[str, MBContainerMountPointConf]] = {}
    logdir: Optional[dict[str, MBContainerMountPointConf]] = {}
    confdir: Optional[dict[str, MBContainerMountPointConf]] = {}
    cachedir: Optional[dict[str, MBContainerMountPointConf]] = {}
    plugindir: Optional[dict[str, MBContainerMountPointConf]] = {}

    def __post_init__(self):
        for mount_type in [
            self.datadir,
            self.logdir,
            self.confdir,
            self.cachedir,
            self.plugindir,
        ]:
            if mount_type:
                for mount_point, conf in mount_type.items():
                    if not is_valid_path(mount_point):
                        raise ValueError(f"Invalid mount point path: {mount_point}")



class MBContainerMetadataConf(Struct):
    create_time: datetime  # format "2025-05-12 05:25:31"
    last_update_time: datetime
    author: str  # Neboer


class MBContainerConf(Struct, kw_only=True):
    image: str
    mount: MBContainerMountConf
    port: list[Tuple[int, int]] = []
    environment: dict[str, str] = {}
    metadata: MBContainerMetadataConf
