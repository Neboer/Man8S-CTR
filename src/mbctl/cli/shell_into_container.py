from mbctl.MBContainer import MBContainer
from mbctl.NerdClient import NerdClient
from mbctl.MBHost.HostEnv import execute_host_command

shell_command = [
    "sh",
    "-c",
    "if [ -x /bin/bash ]; then exec /bin/bash; else exec /bin/sh; fi",
]


# 安全的执行一个shell，如果shell返回错误也不会报错退出。大多数容器内都有一个shell，所以这个函数一般不会失败。
# 如果容器内没有shell，那也不应该用这种方法调试。
# 这种方法要求容器必须正在运行，如果你希望在容器主命令不运行时执行shell，只需要更新容器主命令启动容器再进入shell。
# 我知道这很麻烦，但这是最简单可靠的实现方式，我们不要给NerdClient增加太多复杂功能。
def online_shell(nerd_client: NerdClient, container_name: str) -> int:
    rc = nerd_client.execute_nerdctl_safe(
        ["nerdctl", "exec", "-it", container_name] + shell_command
    )
    return rc[1]  # 返回退出码


# 执行一个网络shell，即使用容器的网络名字空间启动主机中的bash，这个要求通过主机执行命令。
def network_shell(nerd_client: NerdClient, container: MBContainer) -> int:
    # 首先获取容器的PID
    pid = nerd_client.get_container_pid(container.name)
    if pid is None:
        print(f"Container {container.name} is not running.")
        return -1
    # 然后使用nsenter进入网络名字空间
    command = [
        "nsenter",
        "-t",
        str(pid),
        "-n",
        *shell_command,
    ]
    rc = execute_host_command(command)
    return rc
