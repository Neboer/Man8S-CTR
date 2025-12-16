# MBContainer

MBContainer是主要逻辑的位置。实际上，数据流的方向是 MBContainerConf -> MBContainer -> ComposeConf。
MBContainer保存了所有实际的容器信息，还有许多方便操作的方法，而不仅是两边配置文件的结构表示。它由几个不同的部分组成。
其中最重要的部分就是MBContainerMount，它和MBContainer是同一个抽象等级。它可以转换mountconfig，