# nerdclient 是一个用于与 nerdctl 交互的客户端模块，它并不负责处理所有与主机有关的事务——它只与nerdctl通信。

import datetime
from typing import Literal, Optional

from mbctl.NerdClient.CommandExecutor import CommandExecutor
from .NerdContainerInfo import NerdContainerInfo, parse_nerdctl_ps_json_lines
from mbctl.MBLog import mb_logger


class NerdClient(CommandExecutor):
    def list_all_containers(self) -> list[NerdContainerInfo]:
        """列出所有容器。"""
        output = self.execute(
            ["nerdctl", "ps", "-a", "--format", "json"], stdout="pipe"
        )[0]
        if output is None:
            return []
        return parse_nerdctl_ps_json_lines(output)

    def compose_create_container(
        self,
        project_name: str,
        compose_conf: dict,
        pull=False,
        no_failure: bool = False,
    ) -> int:
        """使用 nerdctl compose 创建并运行容器。"""
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile("w+", delete=True) as tmpfile:
            yaml.dump(compose_conf, tmpfile)
            tmpfile.flush()

            prepared_command = [
                "nerdctl",
                "compose",
                "-f",
                tmpfile.name,
                "--project-name",
                project_name,
                "up",
                "-d",
                "--force-recreate",
            ]
            safe = False
            if pull:
                prepared_command += ["--pull", "always"]
            if no_failure:
                safe = True

            _, exec_result = self.execute(prepared_command, safe=safe)
            return exec_result if safe else 0

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
                _, value = self.execute(
                    ["nerdctl", "compose", "-f", tmpfile.name, "run", service_name],
                    safe=True,
                )
                return value
            else:
                self.execute(
                    ["nerdctl", "compose", "-f", tmpfile.name, "run", service_name]
                )
                return 0

    def rename_container(self, old_name: str, new_name: str) -> None:
        """重命名容器。"""
        self.execute(["nerdctl", "rename", old_name, new_name])

    def start_container(self, container_name: str) -> None:
        """启动指定名称的容器。"""
        self.execute(["nerdctl", "start", container_name])

    def stop_and_wait_container(self, container_name: str) -> None:
        """停止指定名称的容器，并等待其完全停止。"""
        self.execute(["nerdctl", "stop", container_name])
        self.execute(["nerdctl", "wait", container_name])

    def stop_and_wait_container_safely(
        self, container_name: str, hide: bool = False
    ) -> int:
        """安全地停止指定名称的容器，并等待其完全停止，返回命令的退出码。如果容器已经退出了，也不会报错。"""
        stdout_conf = "pipe" if hide else "print"
        stderr_conf = "pipe" if hide else "print"
        _, code = self.execute(
            ["nerdctl", "stop", container_name],
            safe=True,
            stdout=stdout_conf,
            stderr=stderr_conf,
        )
        if code != 0:
            return code
        _, code = self.execute(
            ["nerdctl", "wait", container_name],
            safe=True,
            stdout=stdout_conf,
            stderr=stderr_conf,
        )
        return code

    # hide 表示是否隐藏命令的输出。
    def remove_container(
        self, container_name: str, safe: bool = False, hide: bool = False
    ) -> None:
        """删除指定名称的容器。"""
        stdout_conf = "pipe" if hide else "print"
        stderr_conf = "pipe" if hide else "print"
        self.execute(
            ["nerdctl", "rm", "-f", container_name],
            safe=safe,
            stdout=stdout_conf,
            stderr=stderr_conf,
        )

    def shell_execute(
        self,
        container_name: str,
        command: list[str],
    ) -> int:
        """在指定容器中执行命令，返回命令的退出码。"""
        _, code = self.execute(
            ["nerdctl", "exec", "-it", container_name] + command,
            safe=True,
        )
        return code

    def get_container_pid(self, container_name: str) -> int:
        """获取指定容器的主进程 PID。"""
        output, _ = self.execute(
            ["nerdctl", "inspect", "-f", "{{.State.Pid}}", container_name],
            stdout="pipe",
        )
        assert output is not None
        return int(output.strip())

    def get_container_start_time(self, container_name: str) -> datetime.datetime:
        """获取指定容器的启动时间。"""
        output, _ = self.execute(
            ["nerdctl", "inspect", "-f", "{{.State.StartedAt}}", container_name],
            stdout="pipe",
        )
        assert output is not None
        # output is like "2026-02-08T04:42:56.376773929Z"
        return datetime.datetime.fromisoformat(output.strip().rstrip("Z"))

    def monitor_container_logs(
        self,
        container_name: str,
        log_since: Optional[datetime.datetime] = None,
    ) -> None:
        """监视指定容器的日志输出，实时打印到标准输出。

        Args:
            container_name: 容器名称
            log_since: 如果提供，则只显示自该时间点以来的日志
        如果什么也不提供，则显示从现在开始的所有日志。
        """
        log_since_time: Optional[datetime.datetime] = log_since
        if log_since_time is None:
            log_since_time = (
                datetime.datetime.now()
            )  # 如果什么也不提供，则显示从现在开始的所有日志。

        command = [
            "nerdctl",
            "logs",
            "-f",
            "--since",
            log_since_time.isoformat(),
            container_name,
        ]

        self.execute(command, stdout="print", stderr="print")
        return None

    def create_temp_container(self, container_name: str, image_name: str) -> None:
        """创建并启动一个临时容器。

        Args:
            container_name: 临时容器名称
            image_name: 镜像名称
        """
        self.execute(
            [
                "nerdctl",
                "run",
                "-d",
                "--name",
                container_name,
                image_name,
                "sleep",
                "infinity",
            ],
            safe=False,
        )

    def copy_from_container(
        self, container_name: str, container_path: str, host_path: str
    ) -> int:
        """从容器中复制内容到主机。

        规则：源路径 trailing slash 表示复制内容，不带 slash 表示复制整个目录。
        目标路径不应该以 slash 结尾（否则会创建嵌套结构）。

        Args:
            container_name: 容器名称
            container_path: 容器内路径（trailing slash 表示复制内容）
            host_path: 主机目标路径（不应该以 / 结尾）

        Returns:
            命令的退出码
        """
        _, code = self.execute(
            ["nerdctl", "cp", f"{container_name}:{container_path}/", host_path],
            safe=True,
        )
        return code

    def update_container_restart_policy(
        self,
        container_name: str,
        policy: Literal["no", "always", "on-failure", "unless-stopped"],
    ) -> None:
        """更新容器的重启策略。"""
        self.execute(
            ["nerdctl", "update", "--restart", policy, container_name], safe=False
        )
