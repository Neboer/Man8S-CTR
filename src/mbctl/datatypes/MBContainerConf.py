import json
from typing import Any, Optional, Sequence, Tuple, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


def is_valid_path_or_reference(p: str) -> bool:
    # Supports two forms:
    # 1) Absolute path: "/some/host/path"
    # 2) Reference form: "<container-name>:/inner/path"
    if ":" in p:
        name, inner = p.split(":", 1)
        return bool(name) and inner.startswith("/") and ".." not in inner
    return p.startswith("/") and ".." not in p


class MBContainerMountPointConf(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: list[int] = Field(default_factory=lambda: [0, 0])  # [uid, gid]
    source: Optional[str] = None  # source path
    file: bool = False  # whether it's a file mount point
    copyfrom: bool = False  # whether to copy content from image to local path
    perm: Optional[str] = None  # determined based on file flag

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not is_valid_path_or_reference(value):
            raise ValueError(f"Invalid source path: {value}")
        return value

    @model_validator(mode="after")
    def validate_copy_source(self) -> "MBContainerMountPointConf":
        if self.copyfrom and self.source is not None and ":" in self.source:
            raise ValueError(
                f"Copy option source cannot reference other containers: {self.source}"
            )
        return self

    @model_validator(mode="after")
    def set_default_perm(self) -> "MBContainerMountPointConf":
        if self.perm is None:
            self.perm = "644" if self.file else "755"
        return self


class MBContainerMountConf(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: dict[str, MBContainerMountPointConf] = Field(default_factory=dict)
    log: dict[str, MBContainerMountPointConf] = Field(default_factory=dict)
    conf: dict[str, MBContainerMountPointConf] = Field(default_factory=dict)
    cache: dict[str, MBContainerMountPointConf] = Field(default_factory=dict)
    plugin: dict[str, MBContainerMountPointConf] = Field(default_factory=dict)
    socket: dict[str, MBContainerMountPointConf] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mount_points(self) -> "MBContainerMountConf":
        for mount_group in [
            self.data,
            self.log,
            self.conf,
            self.cache,
            self.plugin,
            self.socket,
        ]:
            for mount_point in mount_group:
                if not is_valid_path_or_reference(mount_point):
                    raise ValueError(f"Invalid mount point path: {mount_point}")
        return self


type MBPortPiece = Union[Tuple[int, int], Tuple[int, int, bool]]


def _prune_defaults_for_yaml(data: dict[str, Any]) -> dict[str, Any]:
    """Remove verbose default-only fields so exported YAML stays concise."""
    if not data.get("require"):
        data.pop("require", None)
    if not data.get("local_access"):
        data.pop("local_access", None)

    mount = data.get("mount")
    if isinstance(mount, dict):
        for group_name in list(mount.keys()):
            group = mount[group_name]
            if not isinstance(group, dict) or not group:
                mount.pop(group_name, None)
                continue

            for mount_point_conf in group.values():
                if not isinstance(mount_point_conf, dict):
                    continue

                is_file = bool(mount_point_conf.get("file", False))
                default_perm = "644" if is_file else "755"

                if mount_point_conf.get("owner") == [0, 0]:
                    mount_point_conf.pop("owner", None)
                if mount_point_conf.get("file") is False:
                    mount_point_conf.pop("file", None)
                if mount_point_conf.get("copyfrom") is False:
                    mount_point_conf.pop("copyfrom", None)
                if mount_point_conf.get("perm") == default_perm:
                    mount_point_conf.pop("perm", None)

        if not mount:
            data.pop("mount", None)

    return data


def _to_styled_yaml_node(
    value: Any,
    key: str | None = None,
    parent_key: str | None = None,
) -> Any:
    """Convert python objects to ruamel YAML nodes with mbctl preferred style."""
    if isinstance(value, dict):
        return {
            k: _to_styled_yaml_node(v, str(k), key)
            for k, v in value.items()
        }

    if isinstance(value, list):
        seq = CommentedSeq([
            _to_styled_yaml_node(item, parent_key=key) for item in value
        ])
        if key in {"command", "entrypoint"}:
            seq.fa.set_flow_style()
        return seq

    if isinstance(value, str) and (
        key == "source"
        or parent_key == "environment"
        or parent_key in {"command", "entrypoint"}
    ):
        return DoubleQuotedScalarString(value)

    return value


class MBContainerConf(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: str
    enable_ygg: bool = True
    autostart: bool = True
    require: Sequence[str] = Field(default_factory=list)
    mount: MBContainerMountConf = Field(default_factory=MBContainerMountConf)
    # host_port, container_port, is_udp(optional)
    port: Sequence[MBPortPiece] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)
    # Additional local access hostnames whose Yggdrasil addresses are added to extra_hosts
    local_access: set[str] = Field(default_factory=set)
    # DNS setting for the container
    dns: str = "host"
    extra_compose_configs: dict[str, Any] = Field(default_factory=dict)

    @field_validator("port", mode="before")
    @classmethod
    def normalize_ports(cls, value: Any) -> Sequence[MBPortPiece]:
        if value is None:
            return []

        normalized: list[MBPortPiece] = []
        for entry in value:
            if not isinstance(entry, (list, tuple)):
                raise TypeError("Each port mapping must be a list or tuple.")
            if len(entry) not in (2, 3):
                raise ValueError("Port mapping must have length 2 or 3.")

            host_port, container_port, *rest = entry
            if not isinstance(host_port, int) or not isinstance(container_port, int):
                raise TypeError("Port mapping entries must be integers.")

            if rest:
                normalized.append((host_port, container_port, bool(rest[0])))
            else:
                normalized.append((host_port, container_port))
        return normalized

    @model_validator(mode="after")
    def validate_local_access(self) -> "MBContainerConf":
        if not self.enable_ygg and self.local_access:
            raise ValueError("local_access can only be set when enable_ygg is True.")
        return self

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "MBContainerConf":
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.model_validate(data)

    def to_yaml_file(self, file_path: str) -> None:
        yaml_emitter = YAML()
        yaml_emitter.default_flow_style = False
        yaml_emitter.indent(mapping=2, sequence=4, offset=2)

        yaml_data = _to_styled_yaml_node(
            _prune_defaults_for_yaml(self.model_dump(mode="json", exclude_none=True))
        )

        with open(file_path, "w", encoding="utf-8") as f:
            yaml_emitter.dump(yaml_data, f)

    @staticmethod
    def to_json_schema_file(file_path: str) -> None:
        json_schema = MBContainerConf.model_json_schema()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_schema, f, ensure_ascii=False, indent=2)
