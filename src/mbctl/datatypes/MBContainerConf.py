from typing import Optional, Tuple, Union, Sequence, assert_type
from msgspec import Struct, field, json, yaml
from datetime import datetime

from .MountType import MountType


def is_valid_path_or_reference(p: str) -> bool:
    # 支持两种形式：
    # 1) 绝对路径："/some/host/path"
    # 2) 引用形式："<container-name>:/inner/path"
    if ":" in p:
        name, inner = p.split(":", 1)
        return bool(name) and inner.startswith("/") and ".." not in inner
    return p.startswith("/") and ".." not in p


class MBContainerMountPointConf(Struct, omit_defaults=True, forbid_unknown_fields=True):
    owner: list[int] = field(default_factory=lambda: [0, 0])  # [uid, gid]
    source: Optional[str] = None  # source path
    file: bool = False  # whether it's a file mount point
    perm: Optional[str] = None  # 需要在post init中根据file来设置默认权限

    def __post_init__(self):
        if self.source and not is_valid_path_or_reference(self.source):
            raise ValueError(f"Invalid source path: {self.source}")
        if self.perm is None:
            self.perm = "644" if self.file else "755"


class MBContainerMountConf(Struct, omit_defaults=True, forbid_unknown_fields=True):
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
                    if not is_valid_path_or_reference(mount_point):
                        raise ValueError(f"Invalid mount point path: {mount_point}")


class MBContainerMetadataConf(Struct, kw_only=True):
    create_time: datetime = field(default_factory=datetime.now)
    last_update_time: datetime = field(default_factory=datetime.now)
    author: Optional[str] = ""


type MBPortPiece = Union[Tuple[int, int], Tuple[int, int, bool]]


class MBContainerConf(Struct, kw_only=True, forbid_unknown_fields=True):
    image: str
    enable_ygg: bool = True
    autostart: bool = True
    require: Sequence[str] = []
    mount: MBContainerMountConf = field(default_factory=MBContainerMountConf)
    # host_port, container_port, is_udp(optional)
    # 通常，不建议设置is_udp为false，忽略它即可。
    port: Sequence[tuple] = []
    environment: dict[str, str] = {}
    metadata: MBContainerMetadataConf = field(default_factory=MBContainerMetadataConf)
    # 允许容器本地访问的额外主机名，这些主机名的ygg地址会被添加到extra_hosts中。
    local_access: set[str] = field(default_factory=set)
    # 容器的DNS设置。host表示与主机相同，还可以写成一个具体的容器名字表示使用容器ygg地址当作DNS服务器。也可以写成一个具体的IPv4/IPv6地址。
    dns: str = "host"
    extra_compose_configs: dict = field(default_factory=dict)

    def __post_init__(self):
        for p in self.port:
            assert_type(p, MBPortPiece)  # type: ignore
        if not self.enable_ygg and self.local_access:
            raise ValueError("local_access can only be set when enable_ygg is True.")

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "MBContainerConf":
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()
        return yaml.decode(data, type=MBContainerConf)

    def to_yaml_file(self, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml_data = yaml.encode(self)
            f.write(yaml_data.decode("utf-8"))

    @staticmethod
    def to_json_schema_file(file_path: str) -> None:
        json_schema = json.schema(MBContainerConf)
        with open(file_path, "w", encoding="utf-8") as f:
            json_data = json.encode(json_schema)
            f.write(json_data.decode("utf-8"))
