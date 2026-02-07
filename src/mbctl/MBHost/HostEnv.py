# 执行一些普通Linux都可以执行的功能，比如调用命令。
import subprocess


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
