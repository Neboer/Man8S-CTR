from mbctl.MBContainer import MBContainer
from mbctl.NerdClient import NerdClient
from mbctl.MBHost.UpdateConfig import write_mbcontainer_config
from mbctl.MBHost.Loader import load_mbcontainer_config_by_name
from mbctl.datatypes import MBContainerConf
from mbctl.MBLog import mb_logger


def enable_mbcontainer_autostart(
    nerd_client: NerdClient, container: MBContainer
) -> None:
    container_conf: MBContainerConf = load_mbcontainer_config_by_name(container.name)
    container_conf.autostart = True
    write_mbcontainer_config(container.name, container_conf)
    nerd_client.update_container_restart_policy(container.name, "unless-stopped")
    mb_logger.info(f"Container {container.name} is now set to autostart.")


def disable_mbcontainer_autostart(
    nerd_client: NerdClient, container: MBContainer
) -> None:
    container_conf: MBContainerConf = load_mbcontainer_config_by_name(container.name)
    container_conf.autostart = False
    write_mbcontainer_config(container.name, container_conf)
    nerd_client.update_container_restart_policy(container.name, "no")
    mb_logger.info(f"Container {container.name} is now set to not autostart.")
