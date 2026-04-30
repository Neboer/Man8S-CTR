# Man8S CTR

有关Man8S的详细文档见

https://www.neboer.site/blog/complete-instruction-of-man8s-ctr

## Man8S CTR 的关键概念

### 重启策略

Man8S 底层所使用的 nerdctl 容器自动重启的策略是 unless-stopped。如果停止了 nerdctl 容器，那么即使主机重启，容器也不会自动启动。

Man8S 是类似PM2、systemd-machinectl 的容器编排工具，我们希望每次主机重启时，所有应该自动启动的容器都能自动启动，主机比起是一个容器的宿主，更像是维护一种容器运行的状态。

因此，Man8S 需要 systemd 服务，在主机重启时，systemd 服务会在执行时执行 Man8S 命令，自动启动所有配置文件中设置为自动启动的、并且有 nerdctl 对应容器的容器。

### 容器依赖

Man8S 的容器依赖目前只有在autostart时指定启动顺序的作用，我们希望支持nerdctl新版刚刚加入的对healthcheck检查的支持。