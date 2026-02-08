from typing import Optional
from mbctl.MBContainer import MBContainer, MBContainerTree
from mbctl.NerdClient.NerdClient import NerdClient, NerdContainerInfo


# 表示一个在主机中正在运行的 Man8S 容器
class HostingMBContainer:
    def __init__(
        self, mbcontainer: MBContainer, info: Optional[NerdContainerInfo] = None
    ):
        self.mbcontainer = mbcontainer
        self.info = info
        self.name = mbcontainer.name
        self.container_id = info.id if info else None


def get_hosting_mbcontainers_list(
    mbcontainers: dict[str, MBContainer], infos: list[NerdContainerInfo]
) -> dict[str, HostingMBContainer]:
    """将容器运行信息列表与 Man8S 容器配置进行匹配，返回正在运行的 Man8S 容器及其状态列表。"""
    hosting_containers: dict[str, HostingMBContainer] = {}
    info_dict = {info.names: info for info in infos if info.names}
    
    for container_name, mbcontainer in mbcontainers.items():
        info = info_dict.get(container_name)
        hosting_containers[container_name] = HostingMBContainer(
            mbcontainer=mbcontainer,
            info=info,
        )
    
    return hosting_containers
