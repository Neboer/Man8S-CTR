"""MBContainer 构建逻辑的专用模块。"""

import os
import uuid
from mbctl.NerdClient.NerdClient import NerdClient
from mbctl.MBContainer import MBContainer
from mbctl.MBHost.MakeMountdirs import (
    prepare_mount_entry,
    realize_dir_mount_conf,
    check_mount_path_empty,
    copy_from_container_with_tar,
)
from mbctl.MBLog import mb_logger


def build_mbcontainer(
    container: MBContainer,
    container_name: str,
    client: NerdClient,
    pull: bool = False,
    detach: bool = False,
) -> None:
    """构建并启动一个 Man8S 容器。
    
    Args:
        container: MBContainer 对象
        container_name: 容器名称
        client: NerdClient 实例
        pull: 是否拉取最新镜像
        detach: 是否以分离模式运行
    """
    print(f"Running container: {container_name}")
    
    # 处理挂载点，包括 copyfrom 逻辑
    for entry in container.mount.entries:
        if entry.copyfrom:
            # 如果需要从镜像复制内容，使用临时容器
            _handle_copyfrom_mount(
                client=client,
                container=container,
                entry=entry,
            )
        else:
            # 普通的挂载点准备
            prepare_mount_entry(entry)
    
    # 停止和删除已存在的容器
    client.stop_and_wait_container_safely(container_name, hide=True)
    client.remove_container(container_name, safe=True, hide=True)
    
    # 创建新容器
    client.compose_create_container(
        container_name,
        container.to_compose_conf().to_compose_dict(),
        pull=pull,
    )

    mb_logger.info(f"Container {container_name} created successfully.")
    
    # 如果不是分离模式，显示日志
    if not detach:
        client.next_command_will_execvp()
        client.monitor_container_logs(container_name)


def _handle_copyfrom_mount(
    client: NerdClient,
    container: MBContainer,
    entry,
) -> None:
    """处理 copyfrom 挂载点：从镜像复制内容到主机。
    
    Args:
        client: NerdClient 实例
        container: MBContainer 对象
        entry: MBContainerMountEntry 对象
        
    Raises:
        RuntimeError: 如果目标路径已存在且不为空
    """
    temp_container_name = f"mbctl-copy-{uuid.uuid4().hex[:8]}"
    
    try:
        mb_logger.info(
            f"[copyfrom] Copying content from image {container.image} "
            f"path {entry.target} to {entry.source.real_mount_source_path}"
        )
        
        # 检查目标路径是否为空
        check_mount_path_empty(entry.source.real_mount_source_path)
        
        # 创建挂载目录
        mb_logger.debug(
            f"[copyfrom] Creating mount directory: {entry.source.real_mount_source_path}"
        )
        realize_dir_mount_conf(
            entry.source.real_mount_source_path,
            entry.owner[0],
            entry.owner[1],
            entry.perm,
        )
        mb_logger.debug(
            f"[copyfrom] Mount directory created with owner {entry.owner[0]}:{entry.owner[1]} "
            f"and permissions {entry.perm}"
        )
        
        # 创建临时容器
        mb_logger.debug(
            f"[copyfrom] Creating temporary container: {temp_container_name} from {container.image}"
        )
        client.create_temp_container(temp_container_name, container.image)
        mb_logger.debug(f"[copyfrom] Temporary container created: {temp_container_name}")
        
        try:
            # 使用tar方法从临时容器复制内容到主机，完整保留所有者信息
            mb_logger.debug(
                f"[copyfrom] Copying from {temp_container_name}:{entry.target} to {entry.source.real_mount_source_path}"
            )
            
            code = copy_from_container_with_tar(
                temp_container_name,
                entry.target,
                entry.source.real_mount_source_path,
            )
            
            if code == 0:
                mb_logger.info(
                    f"[copyfrom] Successfully copied content from {container.image}:{entry.target} "
                    f"to {entry.source.real_mount_source_path}"
                )
            else:
                mb_logger.warning(
                    f"[copyfrom] Copy from {container.image}:{entry.target} returned code {code}"
                )
            
            # tar方法已经保留了所有者信息，但仍需设置顶层目录的权限
            mb_logger.debug(
                f"[copyfrom] Setting permissions for mount directory {entry.source.real_mount_source_path}: "
                f"owner={entry.owner[0]}:{entry.owner[1]}, mode={entry.perm}"
            )
            os.chown(entry.source.real_mount_source_path, entry.owner[0], entry.owner[1])
            os.chmod(entry.source.real_mount_source_path, int(entry.perm, 8))
            mb_logger.debug(
                f"[copyfrom] Permissions set successfully for {entry.source.real_mount_source_path}"
            )
            
        finally:
            # 清理临时容器
            mb_logger.debug(f"[copyfrom] Removing temporary container: {temp_container_name}")
            client.remove_container(temp_container_name, safe=True, hide=True)
            mb_logger.debug(f"[copyfrom] Temporary container removed: {temp_container_name}")
            
    except Exception as e:
        mb_logger.error(f"[copyfrom] Error copying content from image: {e}")
        raise
