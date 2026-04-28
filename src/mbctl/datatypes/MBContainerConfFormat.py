"""YAML formatting utilities for MBContainerConf."""
from typing import Any

from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


def _prune_defaults_for_yaml(data: dict[str, Any]) -> dict[str, Any]:
    """Remove verbose default-only fields so exported YAML stays concise."""
    if not data.get("require"):
        data.pop("require", None)
    if not data.get("local_access"):
        data.pop("local_access", None)

    mount = data.get("mount")
    if isinstance(mount, dict):
        # Remove empty mount groups
        for group_name in list(mount.keys()):
            group = mount[group_name]
            if not isinstance(group, dict) or not group:
                mount.pop(group_name, None)
                continue

            # Process mount point configurations
            for mount_point in list(group.keys()):
                mount_point_conf = group[mount_point]
                if not isinstance(mount_point_conf, dict):
                    continue

                is_file = bool(mount_point_conf.get("file", False))
                default_perm = "644" if is_file else "755"

                # Remove default owner [0, 0]
                if mount_point_conf.get("owner") == [0, 0]:
                    mount_point_conf.pop("owner", None)
                # Remove default file=false
                if mount_point_conf.get("file") is False:
                    mount_point_conf.pop("file", None)
                # Remove default copyfrom=false
                if mount_point_conf.get("copyfrom") is False:
                    mount_point_conf.pop("copyfrom", None)
                # Remove default perm based on file type
                if mount_point_conf.get("perm") == default_perm:
                    mount_point_conf.pop("perm", None)
                # Remove null source
                if mount_point_conf.get("source") is None:
                    mount_point_conf.pop("source", None)

                # If mount point is now empty or only has non-default values, keep it
                # If it's empty ({}), we need to represent it
                if not mount_point_conf:
                    # Keep empty dict for mount points without explicit config
                    group[mount_point] = {}

        if not mount:
            data.pop("mount", None)

    return data


def _to_styled_yaml_node(
    value: Any,
    key: str | None = None,
    parent_key: str | None = None,
    is_port_item: bool = False,
) -> Any:
    """Convert python objects to ruamel YAML nodes with mbctl preferred style.
    
    Flow style (JSON-like) is used for:
    - owner fields (lists)
    - command and entrypoint
    - port items (individual [host_port, container_port, ...] tuples)
    
    Block style is used for:
    - port list itself (but items are flow)
    
    Strings are NOT double-quoted unless they contain special YAML characters.
    """
    if isinstance(value, dict):
        return {
            k: _to_styled_yaml_node(v, str(k), key)
            for k, v in value.items()
        }

    if isinstance(value, list):
        seq = CommentedSeq([
            _to_styled_yaml_node(item, parent_key=key, is_port_item=(key == "port"))
            for item in value
        ])
        # Use flow style (JSON-like) for owner, command, entrypoint, and port items
        if key in {"owner", "command", "entrypoint"} or is_port_item:
            seq.fa.set_flow_style()
        return seq

    # For strings, be conservative with quotes - only quote if needed
    if isinstance(value, str) and (
        key == "source"
        or parent_key == "environment"
        or parent_key == "extra_compose_configs"
        or parent_key in {"command", "entrypoint"}
    ):
        return DoubleQuotedScalarString(value)

    return value
