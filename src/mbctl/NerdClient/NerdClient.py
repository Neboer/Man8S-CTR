# nerdclient 是一个用于与 nerdctl 交互的客户端模块，它并不负责处理所有与主机有关的事务——它只与nerdctl通信。

from .NerdContainerInfo import NerdContainerInfo, parse_nerdctl_ps_json_lines
import subprocess

class NerdClient:
    
    def execute_nerdctl_safe(self, cmd: list[str]) -> tuple[str, int]:
        """执行 nerdctl 命令并返回输出和返回码。"""

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        return_code = process.returncode
        if return_code != 0:
            print(f"Error executing command {' '.join(cmd)}:")
            print(stderr)
        return stdout, return_code

    def execute_nerdctl_must(self, cmd: list[str]) -> str:
        """执行 nerdctl 命令，若失败则抛出异常，返回输出。"""
        output, return_code = self.execute_nerdctl_safe(cmd)
        if return_code != 0:
            raise RuntimeError(f"Command {' '.join(cmd)} failed with return code {return_code}")
        return output


    def list_all_containers(self) -> list[NerdContainerInfo]:
        """列出所有容器。"""
        output = self.execute_nerdctl_must(["nerdctl", "ps", "-a", "--format", "json"])
        return parse_nerdctl_ps_json_lines(output)

    def compose_create_container(self, compose_conf: dict) -> None:
        """使用 nerdctl compose 创建容器。"""
        import tempfile
        import yaml
        with tempfile.NamedTemporaryFile("w+", delete=True) as tmpfile:
            yaml.dump(compose_conf, tmpfile)
            tmpfile.flush()
            self.execute_nerdctl_must(["nerdctl", "compose", "-f", tmpfile.name, "up", "-d"])

    def start_container(self, container_name: str) -> None:
        """启动指定名称的容器。"""
        self.execute_nerdctl_must(["nerdctl", "start", container_name])
    
    def stop_and_wait_container(self, container_name: str) -> None:
        """停止指定名称的容器，并等待其完全停止。"""
        self.execute_nerdctl_must(["nerdctl", "stop", container_name])
        self.execute_nerdctl_must(["nerdctl", "wait", container_name])
    
    def remove_container(self, container_name: str) -> None:
        """删除指定名称的容器。"""
        self.execute_nerdctl_must(["nerdctl", "rm", "-f", container_name])

    def shell_execute(
        self,
        container_name: str,
        command: list[str],
    ) -> int:
        """在指定容器中执行命令，返回命令的退出码。"""
        _, code = self.execute_nerdctl_safe(
            ["nerdctl", "exec", "-it", container_name] + command
        )
        return code
    
    def get_container_pid(self, container_name: str) -> int:
        """获取指定容器的主进程 PID。"""
        output = self.execute_nerdctl_must(
            ["nerdctl", "inspect", "-f", "{{.State.Pid}}", container_name]
        )
        return int(output.strip())
