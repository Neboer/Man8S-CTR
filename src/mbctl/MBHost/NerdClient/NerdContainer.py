# 这个文件记载了Nerd容器相关的数据结构，作为python-on-whales返回的Container对象的补充。
from enum import Enum

# 这个数据结构描述一个Nerd容器名字对应的容器可能的三种状态
class NerdContainerState(Enum):
    running = "running"
    stopped = "stopped"
    not_exist = "not_exist"

# 注意，这个状态与 MBContainerStatus 不同，后者是针对MBContainer的运行状态，而此只是针对一个Nerd容器的存在与否及其运行状态。
# 最主要的区别就是，MBContainerStatus中有一个"never"状态，表示这个MBContainer从来没有被创建过，而NerdContainerState中则没有这个状态。
