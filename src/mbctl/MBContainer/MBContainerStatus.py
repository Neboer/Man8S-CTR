from enum import Enum


class MBContainerStatus(Enum):
    never = "never"  # 一个MBContainer容器在硬盘中，但从来没有被containerd创建过
    running = "running"  # 一个MBContainer容器有对应的containerd容器，并且正在运行
    stopped = "stopped"  # 一个MBContainer容器有对应的containerd容器，但当前没有运行
    not_exist = "not_exist"  # 一个MBContainer容器在硬盘中都没有对应的配置文件
    unknown = "unknown"  # 我们并不知道这个容器的状态
