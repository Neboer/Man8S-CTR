# MBContainer

MBContainer是主要逻辑的位置。实际上，数据流的方向是 MBContainerConf -> MBContainer -> ComposeConf。
MBContainer保存了所有实际的容器信息，还有许多方便操作的方法，而不仅是两边配置文件的结构表示。它由几个不同的部分组成。
其中最重要的部分就是MBContainerMount，它和MBContainer是同一个抽象等级。它可以转换mountconfig，

## port 配置

MBContainer中的Port配置，核心是 MBPortPiece = Union[Tuple[int, int], Tuple[int, int, bool]]

实际配置时，往往如下：

```yaml
port:
    - [53, 53] # 将容器的53 tcp 映射到主机 53
    - [53, 53, true] # 将容器的53 udp 映射到主机 53
    - [8080, 80] # 将容器80映射到主机8080
```
省略为false的UDP值，默认键值就是TCP的。

## Mount 配置

```yaml
mount:
    data:
        /data:
            owner: [10001, 10001]
            perm: "755"
        /mnt/data2: {}
        /data3:
            source: /mnt/data/rustfs
    log:
        /log:
            owner: [10001, 10001]
    conf:
        /etc/example_config: {}
        /etc/some_big: {}
        /etc/rustfs.yaml:
            file: true
```

以上是一个容器（比如rustfs）的示例mount配置。默认的owner是0, 0，perm对文件是644，对文件夹是755，file是false。实际在创建容器时，mount配置作为默认配置的更新，成为每个mount块的实际配置。mount下分为六种类型的文件夹，分别为 data log conf cache plugin socket，分别对应在 /var/lib/man8s/<mount_type>/<container_name>/<container_path> 下不同的文件夹，其中container_path为容器中的绝对路径，比如 /var/lib/xxxdata 等等。比如对容器“test-rustfs”来说，它上面配置了的挂载文件夹的默认source其中之一就是 /var/lib/man8s/data/test-rustfs/mnt/data2。对于设置了source的挂载项，如data3，默认source就被实际设置的source覆盖了，改为在主机硬盘中的实际指定的路径。

容器之间可能会共享一些配置，比如容器的某个挂载点可能会保持与其他容器中的某个挂载点相同。这个时候，容器的配置可能会互相引用。Man8S采用的方案是，容器配置有一个“require”属性，容器在这个属性中标注自己依赖哪些容器，如果标记了依赖关系则可以使用它依赖的容器作为参考配置。

容器之间的依赖关系必须是树状的，不能有环。在软件启动之后，所有的Container对象会自动解析成MBContainerTree，然后从下到上依次将“引用”解为真实配置，最后才能完整的解析。

如果，一个容器的mount point中，其source值为"certbot:/cert/neboer.site"，则会自动将certbot容器中，同类型mount point的/cert/neboer.site挂载点的源路径bind到容器中，比如 /var/lib/man8s/data/certbot/cert/neboer.site 这个路径。

