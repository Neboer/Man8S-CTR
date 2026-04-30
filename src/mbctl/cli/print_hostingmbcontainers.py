from .HostingMBContainer import HostingMBContainer
from typing import cast
from mbctl.NerdClient.NerdContainerInfo import NerdContainerStatusKind
from rich.console import Console
from rich.text import Text


console = Console()


def _style_status(hc: HostingMBContainer, status: str) -> Text:
    if hc.info is None or hc.info.status_info is None:
        return Text(status, style="dim")

    status_info = hc.info.status_info
    if status_info.kind == NerdContainerStatusKind.up:
        return Text(status, style="bold green")
    if status_info.kind == NerdContainerStatusKind.created:
        return Text(status, style="bold white")
    if status_info.kind == NerdContainerStatusKind.exited:
        if status_info.exit_code == 0:
            return Text(status, style="bold white")
        return Text(status, style="bold red")
    if status_info.kind == NerdContainerStatusKind.restarting:
        return Text(status, style="bold cyan")
    return Text(status, style="white")


def _style_enable(enable: str) -> Text:
    if enable == "Yes":
        return Text(enable, style="bold green")
    if enable == "No":
        return Text(enable, style="bold red")
    return Text(enable)


def _style_image(image: str) -> Text:
    if "/" not in image:
        return Text(image, style="bold")

    prefix, suffix = image.split("/", 1)
    text = Text()
    text.append(prefix)
    text.append("/")
    text.append(suffix, style="bold")
    return text


def _get_status_display(hc: HostingMBContainer) -> str:
    if hc.info is None or hc.info.status_info is None:
        return "Never"
    return str(hc.info.status_info)


def _append_spaced_cell(
    line: Text,
    raw_value: str,
    width: int,
    spacing: str,
    *,
    align: str = "left",
    styled_value: Text | None = None,
) -> None:
    if align == "center":
        left_pad = max((width - len(raw_value)) // 2, 0)
        right_pad = max(width - len(raw_value) - left_pad, 0)
        line.append(" " * left_pad)
        if styled_value is None:
            line.append(raw_value)
        else:
            line.append_text(styled_value)
        line.append(" " * right_pad)
    else:
        if styled_value is None:
            line.append(raw_value)
        else:
            line.append_text(styled_value)
        line.append(" " * max(width - len(raw_value), 0))

    line.append(spacing)


def print_short_hosting_mbcontainers(
    hosting_containers: dict[str, HostingMBContainer],
) -> None:
    """打印简略的正在运行的 Man8S 容器信息表。"""
    spacing = " "
    headers = ["Container", "Image", "Status", "Enable", "YggAddr"]
    keys = ["container", "image", "status", "enable", "yggaddr"]
    rows: list[dict[str, str | HostingMBContainer]] = []

    for hc in sorted(hosting_containers.values(), key=lambda hc: hc.mbcontainer.name):
        row = {
            "_hc": hc,
            "container": hc.mbcontainer.name,
            "image": hc.mbcontainer.image,
            "status": _get_status_display(hc),
            "enable": "Yes" if hc.mbcontainer.autostart else "No",
            "yggaddr": hc.mbcontainer.yggdrasil_addr or "N/A",
        }
        rows.append(row)

    widths: dict[str, int] = {}
    for key, header in zip(keys, headers):
        widths[key] = len(header)

    for row in rows:
        for key in keys:
            widths[key] = max(widths[key], len(str(row[key])))

    header_line = Text()
    for header, key in zip(headers, keys):
        _append_spaced_cell(
            header_line,
            header,
            widths[key],
            spacing,
            align="center",
            styled_value=Text(header, style="bold"),
        )
    console.print(header_line, no_wrap=True, overflow="ignore")

    for row in rows:
        row_line = Text()
        _append_spaced_cell(
            row_line, str(row["container"]), widths["container"], spacing
        )
        _append_spaced_cell(
            row_line,
            str(row["image"]),
            widths["image"],
            spacing,
            styled_value=_style_image(str(row["image"])),
        )
        _append_spaced_cell(
            row_line,
            str(row["status"]),
            widths["status"],
            spacing,
            styled_value=_style_status(
                cast(HostingMBContainer, row["_hc"]), str(row["status"])
            ),
        )
        _append_spaced_cell(
            row_line,
            str(row["enable"]),
            widths["enable"],
            spacing,
            styled_value=_style_enable(str(row["enable"])),
        )
        _append_spaced_cell(
            row_line, str(row["yggaddr"]), widths["yggaddr"], spacing
        )
        console.print(row_line, no_wrap=True, overflow="ignore")
