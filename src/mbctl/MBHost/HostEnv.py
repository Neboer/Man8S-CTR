# 执行一些普通Linux都可以执行的功能，比如调用命令。
import subprocess
import os


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


def execvp_host_command(command: list[str]) -> None:
    """使用 execvp 替换当前进程为指定命令。"""
    os.execvp(command[0], command)
