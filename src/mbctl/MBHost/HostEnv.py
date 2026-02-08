# 执行一些普通Linux都可以执行的功能，比如调用命令。
import subprocess
import os

# 注意，MBHost与NerdClient完全不同。
# MBHost是直接在主机上执行命令，而NerdClient是通过nerdctl执行命令。
# 虽然 nerdclient 目前来看也是在本地执行命令，但它的职责仅限于与 nerdctl 交互，而不是处理所有主机相关的事务。
# 因此，这里需要一个单独的模块来处理主机命令的执行。
# 当然这里所说的主机，是只运行containerd的云主机，而不是运行mbctl的用户主机。
def execute_host_command(command: list[str], no_failure: bool = False) -> int:
    """在主机上执行一个命令，返回退出码。"""

    try:
        result = subprocess.run(command, check=not no_failure)
        return result.returncode
    except subprocess.CalledProcessError as e:
        if no_failure:
            return e.returncode
        else:
            raise

# 这个函数是非常反设计的。它的意义只是，如果mbctl碰巧与它执行的目标系统是同一个主机，这样mbctl在执行主机命令的时候就可以直接替换当前进程。
def execvp_host_command(command: list[str]) -> None:
    """使用 execvp 替换当前进程为指定命令。"""
    os.execvp(command[0], command)
