# nerdctl api
from typing import Optional
from tempfile import TemporaryDirectory
from mbctl.MBContainer import MBContainer
from mbctl.MBConfig import mb_config
from mbctl.datatypes import ComposeConf
from mbctl.TempfileUtils import change_cwd
from .NerdClientCliWrapper import (
    nerd_ps,
    nerd_get_container_state,
    nerd_start_container,
    nerd_stop_and_wait_container,
    nerd_force_delete_container,
    nerd_compose_up,
    execute_any_command,
    run_cmd,
)
from .NerdContainer import NerdContainerState
from enum import Enum


# 这代表与nerdctl/containerd交互的底层抽象功能。
class NerdClient:
    # 未来，这个函数会支持远程host，从而实现对远程nerdctl的管理。
    def __init__(self, host=None) -> None:
        self.host = host

    def list_running_containers_names(self) -> list[str]:
        # containers = self.client.container.list(all=False)
        # return [container.name for container in containers]
        container_names = nerd_ps(all=False)
        return container_names

    def list_all_containers_names(self) -> list[str]:
        # containers = self.client.container.list(all=True)
        # return [container.name for container in containers]
        container_names = nerd_ps(all=True)
        return container_names

    def get_container_state(self, container_name: str) -> NerdContainerState:
        return nerd_get_container_state(container_name)

    def start_container(self, container_name: str) -> None:
        nerd_start_container(container_name)

    def stop_and_wait_container(self, container_name: str) -> None:
        if self.get_container_state(container_name) == NerdContainerState.running:
            nerd_stop_and_wait_container(container_name)

    def force_delete_container(self, container_name: str) -> None:
        self.stop_and_wait_container(container_name)
        nerd_force_delete_container(container_name)

    def execute_any_command_safely(self, command_args: list) -> int:
        # Run any command without raising even when it fails; return its exit code.
        return run_cmd(command_args, allow_error=True)

    # 这个函数不支持在远程执行
    def compose_create_container(self, compose_conf: ComposeConf):
        with TemporaryDirectory() as tmpdir:
            with change_cwd(tmpdir):
                with open("compose.yaml", "w", encoding="utf-8") as compose_conf_file:
                    compose_conf_file.write(compose_conf.to_compose_yaml_str())
                
                nerd_compose_up()
