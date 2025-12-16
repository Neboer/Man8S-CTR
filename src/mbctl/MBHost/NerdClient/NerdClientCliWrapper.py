# docker-on-wheals 有些时候不好用，它在list container的时候对数据结构的定义有问题。所以我们制作了一个nerdctl命令行的封装。
# 这个函数只是临时代替了一些nerdclient的功能，未来可能会被废弃。
import subprocess
from json import loads
from typing import Optional
from .NerdContainer import NerdContainerState


def run_cmd_get_output(cmd: list[str], allow_error=False) -> tuple[str, int]:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=not allow_error,
    )
    return proc.stdout, proc.returncode


def nerd_ps(all: bool = False) -> list[str]:
    cmd = ["nerdctl", "ps", "--format={{json .Names}}"]
    if all:
        cmd.append("-a")
    output, _ = run_cmd_get_output(cmd)

    return [loads(i) for i in output.splitlines()]


# 这个函数返回None表示容器不存在，True表示运行中，False表示停止。3
def nerd_get_container_state(container_name: str) -> NerdContainerState:
    cmd = ["nerdctl", "inspect", "--format", "{{.State.Running}}", container_name]
    output, return_code = run_cmd_get_output(cmd, True)
    if return_code != 0:
        return NerdContainerState.not_exist
    else:
        if output.strip() == "true":
            return NerdContainerState.running
        else:
            return NerdContainerState.stopped
