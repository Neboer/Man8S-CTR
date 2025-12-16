from typing import Optional, Tuple, Union, Sequence, assert_type
from msgspec import Struct, field
from datetime import datetime
from msgspec import yaml
from .MountType import MountType


def is_valid_path(p: str) -> bool:
    # Simple validation to check if the path is absolute and does not contain illegal characters
    return p.startswith("/") and ".." not in p


class MBContainerMountPointConf(Struct, omit_defaults=True):
    owner: list[int] = field(default_factory=lambda: [0, 0])  # [uid, gid]
    source: Optional[str] = None  # source path
    file: bool = False  # whether it's a file mount point
    perm: Optional[str] = None  # 需要在post init中根据file来设置默认权限

    def __post_init__(self):
        if self.source and not is_valid_path(self.source):
            raise ValueError(f"Invalid source path: {self.source}")
        if self.perm is None:
            self.perm = "644" if self.file else "755"


class MBContainerMountConf(Struct, omit_defaults=True):
    data: dict[str, MBContainerMountPointConf] = {}
    log: dict[str, MBContainerMountPointConf] = {}
    conf: dict[str, MBContainerMountPointConf] = {}
    cache: dict[str, MBContainerMountPointConf] = {}
    plugin: dict[str, MBContainerMountPointConf] = {}

    def __post_init__(self):
        for mount_group in [
            self.data,
            self.log,
            self.conf,
            self.cache,
            self.plugin,
        ]:
            if mount_group:
                for mount_point, conf in mount_group.items():
                    if not is_valid_path(mount_point):
                        raise ValueError(f"Invalid mount point path: {mount_point}")


class MBContainerMetadataConf(Struct, kw_only=True):
    create_time: datetime = field(default_factory=datetime.now)
    last_update_time: datetime = field(default_factory=datetime.now)
    author: Optional[str] = ""


type MBPortPiece = Union[Tuple[int, int], Tuple[int, int, bool]]


class MBContainerConf(Struct, kw_only=True):
    image: str
    enable_ygg: bool = True
    autostart: bool = True
    mount: MBContainerMountConf = field(default_factory=MBContainerMountConf)
    # host_port, container_port, is_udp(optional)
    # 通常，不建议设置is_udp为false，忽略它即可。
    port: Sequence[tuple] = []
    environment: dict[str, str] = {}
    metadata: MBContainerMetadataConf = field(default_factory=MBContainerMetadataConf)

    def __post_init__(self):
        for p in self.port:
            assert_type(p, MBPortPiece) # type: ignore

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "MBContainerConf":
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()
        return yaml.decode(data, type=MBContainerConf)

    def to_yaml_file(self, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml_data = yaml.encode(self)
            f.write(yaml_data.decode("utf-8"))
