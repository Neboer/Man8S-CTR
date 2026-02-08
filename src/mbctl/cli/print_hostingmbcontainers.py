from prettytable import PrettyTable, TableStyle
from .HostingMBContainer import HostingMBContainer


def print_full_hosting_mbcontainers(
    hosting_containers: dict[str, HostingMBContainer],
) -> None:
    """打印完整的正在运行的 Man8S 容器信息表。"""
    table = PrettyTable()
    table.align = "l"
    table.field_names = [
        "Container",
        "ID",
        "Image",
        "Status",
        "AutoStart",
        "YggAddr",
        "Ports",
        "Mounts",
    ]

    # 其中 Mounts 字段是多行显示的。
    for hc in hosting_containers.values():
        mounts_str = "\n".join(hc.mbcontainer.mount.to_mount_short_str_list())
        if hc.info is not None:
            row = [
                hc.mbcontainer.name,
                hc.info.id,
                hc.mbcontainer.image,
                hc.info.status,
                "Yes" if hc.mbcontainer.autostart else "No",
                hc.mbcontainer.yggdrasil_addr or "N/A",
                ", ".join(hc.info.ports) if hc.info.ports else "None",
                mounts_str,
            ]
        else:
            row = [
                hc.mbcontainer.name,
                "N/A",
                hc.mbcontainer.image,
                "Never",
                "Yes" if hc.mbcontainer.autostart else "No",
                hc.mbcontainer.yggdrasil_addr or "N/A",
                "N/A",
                mounts_str,
            ]
        table.add_row(row)

    table.set_style(TableStyle.PLAIN_COLUMNS)
    print(table)


def print_short_hosting_mbcontainers(
    hosting_containers: dict[str, HostingMBContainer],
) -> None:
    """打印简略的正在运行的 Man8S 容器信息表。"""
    table = PrettyTable()
    table.align = "l"
    table.field_names = [
        "Container",
        "Image",
        "Status",
        "AutoStart",
        "YggAddr",
    ]

    for hc in hosting_containers.values():
        short_image_str = (
            hc.mbcontainer.image.split("/", 1)[-1]
            if "/" in hc.mbcontainer.image
            else hc.mbcontainer.image
        )

        table.add_row(
            [
                hc.mbcontainer.name,
                short_image_str,
                hc.info.status if hc.info is not None else "Never",
                "Yes" if hc.mbcontainer.autostart else "No",
                hc.mbcontainer.yggdrasil_addr or "N/A",
            ]
        )
    print(table)
