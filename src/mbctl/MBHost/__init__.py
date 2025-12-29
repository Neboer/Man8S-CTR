from __future__ import annotations

import os
from posixpath import join
from typing import Dict, Optional

from mbctl.network.yggdrasil_addr import get_host_yggdrasil_address_and_subnet
from .NerdClient.NerdClient import NerdClient
from mbctl.MBContainer import MBContainer, MBContainerTree
from mbctl.datatypes import MountType
from mbctl.MBConfig import mb_config


class MBHost:
    def __init__(
        self,
        client: Optional[NerdClient] = None,
        yggaddr: Optional[str] = None,
        yggprefix: Optional[str] = None,
    ) -> None:
        self.client = client if client is not None else NerdClient()

        if yggaddr is None or yggprefix is None:
            ygginfo = get_host_yggdrasil_address_and_subnet()
            self.yggaddr = ygginfo[0]
            self.yggprefix = ygginfo[1]
        else:
            self.yggaddr = yggaddr
            self.yggprefix = yggprefix

        self.config_base_dir = join(mb_config.storage_path, MountType.conf.value)
        os.makedirs(self.config_base_dir, exist_ok=True)

        self._containers_by_name: Dict[str, MBContainer] = {}
        self._container_tree: MBContainerTree
        self._reload_and_resolve_containers()

    def get_container_confdir(self, container_name: str) -> str:
        return join(self.config_base_dir, container_name)

    def get_container_conffile_path(self, container_name: str) -> str:
        return join(self.get_container_confdir(container_name), mb_config.config_file)

    from .mbhost_get_and_resolve_containers import (
        _discover_container_names,
        _ensure_container_loaded,
        _load_container_from_disk,
        _reload_and_resolve_containers,
    )

    from .mbhost_create_container import (
        build_new_container,
        build_all_containers,
        create_container_from_conf,
    )
    
    from .mbhost_get_container import (
        get_container_status,
        get_mbcontainer_conf,
        get_mbcontainer,
    )
    from .mbhost_list_container import list_all_mbcontainer_names, list_containers
    from .mbhost_remove_container import remove_container_mounts
