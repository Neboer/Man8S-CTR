from __future__ import annotations

from typing import Mapping, Optional, Sequence
from mbctl.datatypes import (
    ComposeConf,
    MBContainerConf,
    ComposeServiceConf,
    ComposeNetworkConfig,
)
from .MBContainerMount import MBContainerMount, get_mount_point_src
from .MBContainerPort import MBContainerPortMap
from .MBContainerMetadata import MBContainerMetadata
from .MBContainerStatus import MBContainerStatus
from .MBContainerDNS import DNSType, MBContainerDNS
from mbctl.MBConfig import mb_config
from mbctl.network import string_to_v6suffix
from copy import copy


# MBContainer表示一个从配置文件构造的、便于使用的容器对象。MBContainer并不在构造时解析容器中保存的引用，而是提供一个resolve_references方法来解析引用。
# 使用时，需要先构造MBContainer对象，然后根据其require字段的依赖关系，构造一棵MBContainerTree依赖树，然后从最底层开始依次调用resolve_references方法，最终完成所有容器的引用解析。
class MBContainer:
    def __init__(
        self,
        container_name: str,
        container_conf: MBContainerConf,
        host_yggdrasil_prefix: str,
        status: MBContainerStatus = MBContainerStatus.unknown,
    ):
        self.name = container_name
        self.image = container_conf.image
        self.enable_ygg = container_conf.enable_ygg
        self.autostart = container_conf.autostart
        self.require = container_conf.require
        self.mount = MBContainerMount(container_name, container_conf.mount)
        self.port = MBContainerPortMap(container_conf.port)
        self.environment = container_conf.environment
        self.metadata = MBContainerMetadata(container_conf.metadata)
        self.status = status
        self.resolved = False  # 是否已经完成了解析引用
        # self.local_access 是额外的本地访问主机名列表，不做校验，直接生成对应ygg地址即可。
        self.local_access = container_conf.local_access
        self.dns = MBContainerDNS(container_conf.dns)
        self.extra_compose_configs = container_conf.extra_compose_configs

        self.host_yggdrasil_prefix = host_yggdrasil_prefix
        self.yggdrasil_addr: Optional[str] = None
        if self.enable_ygg:
            self.yggdrasil_addr = string_to_v6suffix(host_yggdrasil_prefix, self.name)
        else:
            if self.dns.type == DNSType.CONTAINER:
                raise ValueError(
                    "Container DNS cannot be of type CONTAINER when Yggdrasil is disabled."
                )

    # reference_contaienrs 是容器间引用的其他容器列表。部分容器的配置文件可能会引用其他容器的配置，所以需要传入这个参数让容器可以获取到其他容器的信息。
    # 注意reference_containers必须是已经完成resolved的MBContainer，MBContainer不应该支持递归解析。
    def resolve_references(
        self, reference_containers: Mapping[str, "MBContainer"] | None = None
    ) -> None:
        refs = reference_containers or {}
        self.mount.resolve_references(refs)
        self.resolved = True

    def to_compose_conf(self) -> ComposeConf:
        """
        Convert the loaded MBContainerConf into a ComposeConf instance.
        """
        network_name = (
            mb_config.network.withygg if self.enable_ygg else mb_config.network.noygg
        )

        restart = "unless-stopped" if self.autostart else "no"

        # 简单的处理一下extra_hosts。将容器自己的名字添加进去，然后再将所有local_access的名字添加进去。
        if self.enable_ygg:
            real_local_access_container_names = copy(self.local_access)
            real_local_access_container_names.add(self.name)
            extra_hosts = {
                f"{ct_name}.{mb_config.local_domain}": string_to_v6suffix(
                    self.host_yggdrasil_prefix, ct_name
                )
                for ct_name in real_local_access_container_names
            }
        else:
            extra_hosts = {}

        compose_service = ComposeServiceConf(
            image=self.image,
            container_name=self.name,
            hostname=self.name,
            networks=[network_name],
            volumes=self.mount.to_compose_volumes(),
            ports=self.port.to_compose_ports(),
            environment=self.environment,
            restart=restart,
            extra_hosts=extra_hosts,
            dns=self.dns.to_compose_dns_entry(self.host_yggdrasil_prefix),
        )

        return ComposeConf(
            extra_compose_configs=self.extra_compose_configs,
            services={self.name: compose_service},
            networks={network_name: ComposeNetworkConfig(external=True)}
        )
