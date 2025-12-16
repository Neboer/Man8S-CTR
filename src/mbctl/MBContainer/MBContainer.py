from typing import Optional, Sequence
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
        self.mount = MBContainerMount(container_name, container_conf.mount)
        self.port = MBContainerPortMap(container_conf.port)
        self.environment = container_conf.environment
        self.metadata = MBContainerMetadata(container_conf.metadata)
        self.status = status

        self.yggdrasil_addr: Optional[str] = None
        if self.enable_ygg:
            self.yggdrasil_addr = string_to_v6suffix(
                host_yggdrasil_prefix, self.name
            )

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
            mount=mount_conf,
            port=port_conf,
            environment=self.environment,
            metadata=self.metadata.to_mbcontainer_metadata_conf(),
        )
