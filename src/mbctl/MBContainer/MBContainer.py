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
from mbctl.MBConfig import mb_config
from mbctl.network import string_to_v6suffix

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

        self.yggdrasil_addr: Optional[str] = None
        if self.enable_ygg:
            self.yggdrasil_addr = string_to_v6suffix(host_yggdrasil_prefix, self.name)

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

        compose_service = ComposeServiceConf(
            image=self.image,
            container_name=self.name,
            hostname=self.name,
            networks=[network_name],
            volumes=self.mount.to_compose_volumes(),
            ports=self.port.to_compose_ports(),
            environment=self.environment,
            restart=restart,
        )

        return ComposeConf(
            services={self.name: compose_service},
            networks={network_name: ComposeNetworkConfig()},
        )

    def to_mbcontainer_conf(self) -> MBContainerConf:
        """
        Convert the MBContainer instance back to MBContainerConf.
        """
        mount_conf = self.mount.to_mbcontainer_mount_conf()
        port_conf = self.port.to_mbcontainer_port_conf()

        return MBContainerConf(
            image=self.image,
            enable_ygg=self.enable_ygg,
            autostart=self.autostart,
            require=self.require,
            mount=mount_conf,
            port=port_conf,
            environment=self.environment,
            metadata=self.metadata.to_mbcontainer_metadata_conf(),
        )
