# 将当前的进程使用 execv 替换为进入指定容器的 shell。
from mbctl.MBContainer import MBContainer
from mbctl.NerdClient import NerdClient
from mbctl.MBHost.HostEnv import execute_host_command, execvp_host_command
import os

shell_command = [
    "sh",
    "-c",
    "if [ -x /bin/bash ]; then exec /bin/bash; else exec /bin/sh; fi",
]


# 安全的执行一个shell
# 这种方法要求容器必须正在运行，如果你希望在容器主命令不运行时执行shell，只需要更新容器主命令启动容器再进入shell。
def online_shell(nerd_client: NerdClient, container_name: str) -> None:
    execvp_host_command(
        ["nerdctl", "exec", "-it", container_name] + shell_command,
    )


# 执行一个网络shell，即使用容器的网络名字空间启动主机中的bash，这个要求通过主机执行命令。
def network_shell(nerd_client: NerdClient, container: MBContainer) -> None:
    # 首先获取容器的PID
    pid = nerd_client.get_container_pid(container.name)
    if pid is None:
        print(f"Container {container.name} is not running.")
        return
    # 然后使用nsenter进入网络名字空间
    command = [
        "nsenter",
        "-t",
        str(pid),
        "-n",
        *shell_command,
    ]
    execvp_host_command(command)
