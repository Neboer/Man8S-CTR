# MBContainer

MBContainer是主要逻辑的位置。实际上，数据流的方向是 MBContainerConf -> MBContainer -> ComposeConf。
MBContainer保存了所有实际的容器信息，还有许多方便操作的方法，而不仅是两边配置文件的结构表示。它由几个不同的部分组成。
其中最重要的部分就是MBContainerMount，它和MBContainer是同一个抽象等级。它可以转换mountconfig，

## port配置

MBContainer中的Port配置，核心是 MBPortPiece = Union[Tuple[int, int], Tuple[int, int, bool]]

实际配置时，往往如下：

```yaml
port:
    - [53, 53] # 将容器的53 tcp 映射到主机 53
    - [53, 53, true] # 将容器的53 udp 映射到主机 53
    - [8080, 80] # 将容器80映射到主机8080
```
省略为false的UDP值，默认键值就是TCP的。