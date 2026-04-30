from .HostingMBContainer import HostingMBContainer


def print_table(headers, rows, column_spacing=2):
    """
    打印对齐的表格，表头居中，数据行左对齐。
    
    Args:
        headers: 表头列表
        rows: 数据行列表，每行是一个列表
        column_spacing: 列之间的间距，默认2个空格
    """
    # 计算每列的最大宽度
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 打印表头（居中）
    header_parts = []
    for i, h in enumerate(headers):
        width = col_widths[i]
        header_parts.append(str(h).center(width))
    print((' ' * column_spacing).join(header_parts))
    
    # 打印数据行（左对齐）
    for row in rows:
        row_parts = []
        for i, cell in enumerate(row):
            width = col_widths[i]
            row_parts.append(str(cell).ljust(width))
        print((' ' * column_spacing).join(row_parts))


def print_short_hosting_mbcontainers(
    hosting_containers: dict[str, HostingMBContainer],
) -> None:
    """打印简略的正在运行的 Man8S 容器信息表。"""
    headers = [
        "Container",
        "Image",
        "Status",
        "Enable",
        "YggAddr",
    ]
    rows = []

    for hc in sorted(hosting_containers.values(), key=lambda hc: hc.mbcontainer.name):
        short_image_str = (
            hc.mbcontainer.image.split("/", 1)[-1]
            if "/" in hc.mbcontainer.image
            else hc.mbcontainer.image
        )

        row = [
            hc.mbcontainer.name,
            short_image_str,
            str(hc.info.status_info) if hc.info is not None else "Never",
            "Yes" if hc.mbcontainer.autostart else "No",
            hc.mbcontainer.yggdrasil_addr or "N/A",
        ]
        rows.append(row)
    
    print_table(headers, rows, column_spacing=2)
