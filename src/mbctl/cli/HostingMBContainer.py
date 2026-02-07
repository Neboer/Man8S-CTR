from mbctl.MBContainer import MBContainer, MBContainerTree
from mbctl.NerdClient.NerdClient import NerdClient, NerdContainerInfo

# 表示一个在主机中正在运行的 Man8S 容器
class HostingMBContainer:
    def __init__(self, mbcontainer: MBContainer, info: NerdContainerInfo):
        self.mbcontainer = mbcontainer
        self.info = info
        self.name = mbcontainer.name
        self.container_id = info.id


def get_hosting_mbcontainers_list(
    mbcontainers: dict[str, MBContainer], infos: list[NerdContainerInfo]
) -> dict[str, HostingMBContainer]:
    """将容器运行信息列表与 Man8S 容器配置进行匹配，返回正在运行的 Man8S 容器及其状态列表。"""
    hosting_containers: list[HostingMBContainer] = []
    for info in infos:
        if info.names:
            container_name = info.names[0].lstrip("/")
            if container_name in mbcontainers:
                hosting_containers.append(
                    HostingMBContainer(
                        mbcontainer=mbcontainers[container_name],
                        info=info,
                    )
                )
    return {hc.name: hc for hc in hosting_containers}
