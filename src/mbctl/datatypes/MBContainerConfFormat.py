"""YAML formatting utilities for MBContainerConf.

This module provides utilities for handling YAML serialization and RoundTrip updates.
It is used internally by UpdateConfig for updating container configurations while
preserving YAML comments and formatting. Do NOT use this module from other projects.

Key functions:
- update_mbcontainer_autostart(): RoundTrip update of autostart field in YAML file
"""
from typing import Any
import os

from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml import YAML

# 这个实现得并不好，太过死板，只能改autostart。未来会考虑更通用的实现。
def update_mbcontainer_autostart(file_path: str, autostart: bool) -> None:
    """Update the autostart field in a MBContainerConf YAML file via RoundTrip.
    
    This preserves comments, formatting, and all other content in the file.
    
    Args:
        file_path: Path to the YAML file
        autostart: New autostart value (boolean)
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    # Preserve indentation to keep original formatting
    yaml.indent(mapping=2, sequence=2, offset=2)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Read existing file
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.load(f)
    else:
        data = {}
    
    # Update autostart field
    data["autostart"] = autostart
    
    # Write back, preserving format
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


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
