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
            raise RuntimeError(
                f"Command {' '.join(cmd)} failed with return code {return_code}"
            )
        return output

    def list_all_containers(self) -> list[NerdContainerInfo]:
        """列出所有容器。"""
        output = self.execute_nerdctl_must(["nerdctl", "ps", "-a", "--format", "json"])
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
                _, value = self.execute_nerdctl_safe(prepared_command)
                return value
            else:
                self.execute_nerdctl_must(prepared_command)
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
                _, value = self.execute_nerdctl_safe(
                    ["nerdctl", "compose", "-f", tmpfile.name, "run", service_name]
                )
                return value
            else:
                self.execute_nerdctl_must(
                    ["nerdctl", "compose", "-f", tmpfile.name, "run", service_name]
                )
                return 0

    def rename_container(self, old_name: str, new_name: str) -> None:
        """重命名容器。"""
        self.execute_nerdctl_must(["nerdctl", "rename", old_name, new_name])

    def start_container(self, container_name: str) -> None:
        """启动指定名称的容器。"""
        self.execute_nerdctl_must(["nerdctl", "start", container_name])

    def stop_and_wait_container(self, container_name: str) -> None:
        """停止指定名称的容器，并等待其完全停止。"""
        self.execute_nerdctl_must(["nerdctl", "stop", container_name])
        self.execute_nerdctl_must(["nerdctl", "wait", container_name])

    def stop_and_wait_container_safely(self, container_name: str) -> int:
        """安全地停止指定名称的容器，并等待其完全停止，返回命令的退出码。如果容器已经退出了，也不会报错。"""
        _, code = self.execute_nerdctl_safe(["nerdctl", "stop", container_name])
        if code != 0:
            return code
        _, code = self.execute_nerdctl_safe(["nerdctl", "wait", container_name])
        return code

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
