# 将 MBContainer 转换成 docker-compose 配置文件然后启动运行。
# 对应main中的 run rerun 命令。

from mbctl.MBContainer.MBContainer import MBContainer
from mbctl.MBHost.MakeMountdirs import realize_dir_mount_conf
from mbctl.NerdClient.NerdClient import NerdClient
from mbctl.cli.HostingMBContainer import HostingMBContainer


# 启动指定的容器的核心步骤。我们这里要假定容器可能是已经启动过一遍的了。
# 获取containers比较昂贵，所以我们只在需要调用它的时候（如update_and_rerun）才调用它。
# 用户需要为自己输入的命令负责，mbctl并不是轮椅，你要知道你在干什么。
def run_container(mbcontainer: MBContainer, nerd_client: NerdClient, pull: bool = False) -> None:
    """启动一个 Man8S 容器，要求必须是一个全新的容器。"""
    # 1. 确保挂载点目录存在。
    for mount_entry in mbcontainer.mount.mount_points:
        if not mount_entry.file:  # 只创建目录挂载点，跳过文件挂载点。
            realize_dir_mount_conf(
                mount_entry.source.real_mount_source_path,
                mount_entry.owner[0],
                mount_entry.owner[1],
                mount_entry.perm,
            )

        # 2. 使用 NerdClient 启动容器。
        nerd_client.compose_create_container(mbcontainer.to_compose_conf().to_compose_dict(), pull=pull)
