from typing import Dict
from mbctl.datatypes import (
    MBContainerConf,
    ComposeConf,
    ComposeServiceConf,
    ComposeNetworkConfig,
)
from .MountConf import convert_mount_to_info
from .PortConf import convert_port_conf
from mbctl.MBConfig import mb_config


def convert_full_conf(
    mbcontainer_conf: MBContainerConf, container_name: str, yggbridge: bool = True
) -> ComposeConf:

    bind_mounts = convert_mount_to_info(mbcontainer_conf.mount, container_name)

    network_name = mb_config.network.withygg if yggbridge else mb_config.network.noygg

    compose_service = ComposeServiceConf(
        image=mbcontainer_conf.image,
        container_name=container_name,
        hostname=container_name,
        networks=[network_name],
        volumes=[":".join(m) for m in bind_mounts],
        ports=convert_port_conf(mbcontainer_conf.port),
        environment=mbcontainer_conf.environment,
    )

    compose_conf = ComposeConf(
        services={container_name: compose_service},
        networks={network_name: ComposeNetworkConfig()},
    )

    return compose_conf
