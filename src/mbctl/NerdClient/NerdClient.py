# nerdclient 是一个用于与 nerdctl 交互的客户端模块，它并不负责处理所有与主机有关的事务——它只与nerdctl通信。

from typing import Literal, Optional
from .NerdContainerInfo import NerdContainerInfo, parse_nerdctl_ps_json_lines
import subprocess


class NerdClient:

    def execute_nerdctl(
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

    def list_all_containers(self) -> list[NerdContainerInfo]:
        """列出所有容器。"""
        output = self.execute_nerdctl(["nerdctl", "ps", "-a", "--format", "json"], stdout="pipe")[0]
        if output is None:
            return []
        return parse_nerdctl_ps_json_lines(output)

    def compose_create_container(
        self, compose_conf: dict, pull = False, no_failure: bool = False
    ) -> int:
        """使用 nerdctl compose 创建并运行容器。"""
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile("w+", delete=True) as tmpfile:
            yaml.dump(compose_conf, tmpfile)
            tmpfile.flush()

            prepared_command = ["nerdctl", "compose", "-f", tmpfile.name, "up", "-d", "--force-recreate"]
            if pull:
                prepared_command += ["--pull", "always"]
            if no_failure:
                _, value = self.execute_nerdctl(prepared_command, safe=True)
                return value
            else:
                self.execute_nerdctl(prepared_command, safe=False)
                return 0

    def compose_run_temp(
        self, temp_compose_conf: dict, no_failure: bool = False
    ) -> int:
        """使用 nerdctl compose 创建并 run 运行一个临时容器。"""
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile("w+", delete=True) as tmpfile:
            service_name = list(temp_compose_conf["services"].keys())[0]
            yaml.dump(temp_compose_conf, tmpfile)
            tmpfile.flush()
            if no_failure:
                _, value = self.execute_nerdctl(
                    ["nerdctl", "compose", "-f", tmpfile.name, "run", service_name],
                    safe=True,
                )
                return value
            else:
                self.execute_nerdctl(["nerdctl", "compose", "-f", tmpfile.name, "run", service_name])
                return 0

    def rename_container(self, old_name: str, new_name: str) -> None:
        """重命名容器。"""
        self.execute_nerdctl(["nerdctl", "rename", old_name, new_name])

    def start_container(self, container_name: str) -> None:
        """启动指定名称的容器。"""
        self.execute_nerdctl(["nerdctl", "start", container_name])

    def stop_and_wait_container(self, container_name: str) -> None:
        """停止指定名称的容器，并等待其完全停止。"""
        self.execute_nerdctl(["nerdctl", "stop", container_name])
        self.execute_nerdctl(["nerdctl", "wait", container_name])

    def stop_and_wait_container_safely(self, container_name: str) -> int:
        """安全地停止指定名称的容器，并等待其完全停止，返回命令的退出码。如果容器已经退出了，也不会报错。"""
        _, code = self.execute_nerdctl(["nerdctl", "stop", container_name], safe=True)
        if code != 0:
            return code
        _, code = self.execute_nerdctl(["nerdctl", "wait", container_name], safe=True)
        return code

    def remove_container(self, container_name: str) -> None:
        """删除指定名称的容器。"""
        self.execute_nerdctl(["nerdctl", "rm", "-f", container_name])

    def shell_execute(
        self,
        container_name: str,
        command: list[str],
    ) -> int:
        """在指定容器中执行命令，返回命令的退出码。"""
        _, code = self.execute_nerdctl(
            ["nerdctl", "exec", "-it", container_name] + command,
            safe=True,
        )
        return code

    def get_container_pid(self, container_name: str) -> int:
        """获取指定容器的主进程 PID。"""
        output, _ = self.execute_nerdctl(
            ["nerdctl", "inspect", "-f", "{{.State.Pid}}", container_name], stdout="pipe"
        )
        assert output is not None
        return int(output.strip())
