from mbctl.network.yggdrasil_addr import get_host_yggdrasil_address_and_subnet
from .NerdClient.NerdClient import NerdClient
from mbctl.MBContainer import get_mount_point_src
from mbctl.datatypes import MountType
from posixpath import join
from mbctl.MBConfig import mb_config


class MBHost:
    def __init__(self) -> None:
        self.client = NerdClient()

        ygginfo = get_host_yggdrasil_address_and_subnet()
        self.yggaddr = ygginfo[0]
        self.yggprefix = ygginfo[1]

        self.config_base_dir = join(mb_config.storage_path, MountType.conf.value)

    def get_container_confdir(self, container_name: str) -> str:
        return join(self.config_base_dir, container_name)

    def get_container_conffile_path(self, container_name: str) -> str:
        return join(self.get_container_confdir(container_name), mb_config.config_file)

    from .mbhost_create_container import build_new_container, create_container_from_conf
    from .mbhost_get_container import (
        get_container_status,
        get_mbcontainer_conf,
        get_mbcontainer,
    )
    from .mbhost_list_container import list_all_mbcontainer_names, list_containers
    from .mbhost_remove_container import remove_container_mounts
