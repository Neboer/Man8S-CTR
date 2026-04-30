import os
import subprocess
from mbctl.MBContainer.MBContainerMount import MBContainerMountEntry
from mbctl.MBLog import mb_logger


def check_mount_path_empty(mount_path: str) -> None:
    """检查挂载路径是否为空。

    Args:
        mount_path: 要检查的挂载路径

    Raises:
        RuntimeError: 如果路径已存在且不为空
    """
    if os.path.exists(mount_path):
        if os.listdir(mount_path):
            error_msg = (
                f"Mount path {mount_path} already exists and is not empty. "
                f"Cannot proceed with copyfrom operation."
            )
            mb_logger.error(f"[mount] {error_msg}")
            raise RuntimeError(error_msg)
        else:
            mb_logger.debug(f"[mount] Mount path exists but is empty: {mount_path}")
    else:
        mb_logger.debug(f"[mount] Mount path does not exist, will create: {mount_path}")


def copy_from_container_with_tar(
    container_name: str, container_path: str, host_path: str
) -> int:
    """使用tar命令从容器复制内容到主机，完整保留所有者信息。
    
    该函数使用 nerdctl exec + tar 的方式，类似于：
    nerdctl exec container tar -C /path --numeric-owner -cpf - . \
    | tar -C /host/path --numeric-owner -xpf -
    
    这种方式能够大量保留文件的所有者、权限等信息。
    注意：由于容器内可能使用BusyBox tar，不支持--xattrs和--acls选项，所以省略这些选项。
    
    Args:
        container_name: 容器名称
        container_path: 容器内的源路径
        host_path: 主机目标路径
        
    Returns:
        命令的退出码，0表示成功
        
    Raises:
        RuntimeError: 如果复制失败
    """
    mb_logger.debug(
        f"[copyfrom] Using tar method to copy from {container_name}:{container_path} to {host_path}"
    )

    # 构建源命令：在容器中执行 tar 打包
    source_cmd = [
        "nerdctl",
        "exec",
        container_name,
        "tar",
        "-C",
        container_path,
        "--numeric-owner",
        "-cpf",
        "-",
        ".",
    ]

    # 构建目标命令：在主机上执行 tar 解包
    target_cmd = ["tar", "-C", host_path, "--numeric-owner", "-xpf", "-"]

    try:
        # 启动源进程（打包）
        source_process = subprocess.Popen(
            source_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # 启动目标进程（解包），连接到源进程的输出
        target_process = subprocess.Popen(
            target_cmd,
            stdin=source_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 关闭源进程的stdout，让管道正常工作
        if source_process.stdout:
            source_process.stdout.close()

        # 等待两个进程完成（使用communicate()正确处理所有I/O）
        target_stdout, target_stderr = target_process.communicate()
        target_returncode = target_process.returncode

        source_stdout, source_stderr = source_process.communicate()
        source_returncode = source_process.returncode

        # 检查返回码
        if source_returncode != 0:
            error_msg = f"Source tar command failed with code {source_returncode}"
            if source_stderr:
                stderr_output = source_stderr.decode("utf-8", errors="replace")
                if stderr_output:
                    error_msg += f": {stderr_output}"
            mb_logger.error(f"[copyfrom] {error_msg}")
            raise RuntimeError(error_msg)

        if target_returncode != 0:
            error_msg = f"Target tar command failed with code {target_returncode}"
            if target_stderr:
                stderr_text = target_stderr.decode("utf-8", errors="replace")
                if stderr_text:
                    error_msg += f": {stderr_text}"
            mb_logger.error(f"[copyfrom] {error_msg}")
            raise RuntimeError(error_msg)

        mb_logger.debug(
            f"[copyfrom] Successfully copied using tar method from {container_name}:{container_path} to {host_path}"
        )
        return 0

    except Exception as e:
        mb_logger.error(f"[copyfrom] Error during tar copy: {e}")
        raise


def prepare_mount_entry(mount_entry: MBContainerMountEntry) -> None:
    """对一个挂载点进行准备工作（创建目录或检查文件存在性）。

    注意：如果需要从镜像复制内容，应该在调用此函数之前由上层（cli/main）处理。
    此函数只负责创建目录或检查文件是否存在。
    """

    def change_entry_perm():
        try:
            os.chown(
                mount_entry.source.real_mount_source_path,
                mount_entry.owner[0],
                mount_entry.owner[1],
            )
            os.chmod(
                mount_entry.source.real_mount_source_path, int(mount_entry.perm, 8)
            )
        except PermissionError as e:
            mb_logger.info(f"Change dir permission error: {e}, continue...")

    if not mount_entry.file:  # 只创建目录挂载点，跳过文件挂载点。
        # 为什么要跳过？因为自动创建文件挂载点甚至只是创建它的父目录都会引起极大的困惑。
        os.makedirs(mount_entry.source.real_mount_source_path, exist_ok=True)
        change_entry_perm()
    else:
        # 如果是文件挂载点，则检查此挂载点的实际源文件是否存在，如果不存在则报错并不要创建。
        if not os.path.exists(mount_entry.source.real_mount_source_path):
            raise FileNotFoundError(
                f"Mount source file {mount_entry.source} does not exist."
            )
        elif not os.path.isfile(mount_entry.source.real_mount_source_path):
            raise FileNotFoundError(f"Mount source {mount_entry.source} is not a file.")
        else:
            # 如果文件存在，则应用正确的权限设置
            change_entry_perm()
