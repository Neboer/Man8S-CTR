from __future__ import annotations

from collections.abc import Mapping, MutableSet

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from mbctl.NerdClient.NerdContainerInfo import NerdContainerStatusKind

from .HostingMBContainer import HostingMBContainer


console = Console()


def _style_container_name(hc: HostingMBContainer) -> Text:
    text_style = ""
    if hc.mbcontainer.autostart:
        text_style += "bold "
    if hc.info is None or hc.info.status_info is None:
        return Text(hc.mbcontainer.name, style=text_style + "dim")

    status_info = hc.info.status_info
    if status_info.kind == NerdContainerStatusKind.up:
        return Text(hc.mbcontainer.name, style=text_style + "green")

    return Text(hc.mbcontainer.name, style=text_style + "white")


def _add_dependency_branches(
    branch: Tree,
    container_name: str,
    hosting_containers: Mapping[str, HostingMBContainer],
    *,
    path: MutableSet[str],
) -> None:
    hc = hosting_containers.get(container_name)
    if hc is None:
        branch.add(Text(container_name, style="dim"))
        return

    dependencies = sorted(set(hc.mbcontainer.require))
    for dependency_name in dependencies:
        dependency_hc = hosting_containers.get(dependency_name)
        if dependency_hc is None:
            branch.add(Text(dependency_name, style="dim"))
            continue

        child_branch = branch.add(_style_container_name(dependency_hc))
        if dependency_name in path:
            continue

        path.add(dependency_name)
        try:
            _add_dependency_branches(
                child_branch,
                dependency_name,
                hosting_containers,
                path=path,
            )
        finally:
            path.remove(dependency_name)


def build_tree_hosting_mbcontainers(
    hosting_containers: dict[str, HostingMBContainer],
) -> Tree:
    """Build a Rich tree showing containers and their dependency hierarchy."""
    tree = Tree(Text("Managed containers", style="bold"), guide_style="bold bright_blue")

    required_names = {
        dependency_name
        for hc in hosting_containers.values()
        for dependency_name in hc.mbcontainer.require
    }
    root_names = sorted(
        name for name in hosting_containers.keys() if name not in required_names
    )

    for root_name in root_names:
        root_hc = hosting_containers[root_name]
        root_branch = tree.add(_style_container_name(root_hc))
        _add_dependency_branches(
            root_branch,
            root_name,
            hosting_containers,
            path={root_name},
        )

    # Some dependency graphs may not have a unique root if every container is required
    # by something else. In that case, fall back to showing any missing roots directly
    # so the command still prints the full set of managed containers.
    if not root_names:
        for hc in sorted(hosting_containers.values(), key=lambda hc: hc.mbcontainer.name):
            tree.add(_style_container_name(hc))

    return tree


def print_tree_hosting_mbcontainers(
    hosting_containers: dict[str, HostingMBContainer],
    *,
    console: Console = console,
) -> None:
    """Print a Rich tree of managed container names."""
    console.print(build_tree_hosting_mbcontainers(hosting_containers))