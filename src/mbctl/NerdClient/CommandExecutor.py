# 执行命令的工具类。
# 它拥有多种执行命令的模式，同时还支持转换成“执行下一条命令之后将本进程替换”的功能，
import subprocess
from typing import Optional
from typing_extensions import Literal
import os


# nerdctl永远是在本地执行的，是不是可以考虑把nerdclient类给直接干掉？
# 在这里需要做一个 execute_execvp，它直接调用 os.execvp 来替换当前进程。
# 无论在任何时候（本地还是远程），nerdctl 命令都是在本地执行的，这个非常重要！因此没必要nerdclient了吧。。。
# 毕竟在ssh里执行命令的成本太高，还不如直接把整个工具装进ssh。
class CommandExecutor:

    def __init__(self, next_command_execvp: bool = False) -> None:
        self._next_command_execvp = next_command_execvp

    def next_command_will_execvp(self) -> None:
        """设置下一个命令将使用 execvp 替换当前进程。"""
        self._next_command_execvp = True

    def _execute_command(
        self,
        cmd: list[str],
        safe: bool = False,
        stdout: Literal["pipe", "print"] = "print",
        stderr: Literal["pipe", "print"] = "print",
    ) -> tuple[Optional[str], int]:
        """执行 nerdctl 命令。

        Args:
            cmd: 命令列表
            safe: 如果为False，错误时立即抛出异常；如果为True，返回输出和返回码
            stdout: "pipe"捕获输出，"print"让进程自由打印
            stderr: "pipe"捕获错误输出，"print"让进程自由打印

        Returns:
            (输出, 返回码) - 输出为None时表示无捕获或未打印
        """
        stdout_setting = subprocess.PIPE if stdout == "pipe" else None
        stderr_setting = subprocess.PIPE if stderr == "pipe" else None

        process = subprocess.Popen(
            cmd,
            stdout=stdout_setting,
            stderr=stderr_setting,
            text=True,
        )
        out, err = process.communicate()
        return_code = process.returncode

        if not safe and return_code != 0:
            print(f"Error executing command {' '.join(cmd)}:")
            print(err)
            raise RuntimeError(
                f"Command {' '.join(cmd)} failed with return code {return_code}"
            )

        if return_code != 0:
            print(f"Error executing command {' '.join(cmd)}:")
            print(err)

        output = out if stdout == "pipe" else None
        return output, return_code

    def _execute_execvp(self, cmd: list[str]) -> None:
        """使用 execvp 替换当前进程为指定命令。"""

        os.execvp(cmd[0], cmd)

    # 通用执行函数，根据 next_command_execvp 决定是执行命令还是 execvp 替换进程
    def execute(
        self,
        cmd: list[str],
        safe: bool = False,
        stdout: Literal["pipe", "print"] = "print",
        stderr: Literal["pipe", "print"] = "print",
    ) -> tuple[Optional[str], int]:
        if self._next_command_execvp:
            self._execute_execvp(cmd)
            return None, 0  # 实际上不会返回
        else:
            return self._execute_command(cmd, safe=safe, stdout=stdout, stderr=stderr)
