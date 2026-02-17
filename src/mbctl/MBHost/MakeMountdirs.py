import os
import uuid
from mbctl.MBContainer.MBContainerMount import MBContainerMountEntry
from mbctl.MBLog import mb_logger

def copy_from_image(
    image_name: str, image_path: str, host_mount_path: str, uid: int, gid: int, perm: str
) -> None:
    """Copy content from an image path to the host mount path using a temporary container.
    
    This function:
    1. Creates a temporary bare container from the image (no process runs)
    2. Copies content from image path to host path using nerdctl cp
    3. Sets owner and permissions
    4. Cleans up the temporary container
    """
    from mbctl.NerdClient.NerdClient import NerdClient
    
    client = NerdClient()
    data_container_name = f"mbctl-copy-{uuid.uuid4().hex[:8]}"
    
    try:
        # Create the host mount directory first
        os.makedirs(host_mount_path, exist_ok=True)
        
        mb_logger.debug(
            f"Copying content from {image_name}:{image_path} to {host_mount_path}"
        )
        
        # Create a temporary data container that we can copy from
        # We use /bin/true as entrypoint so it doesn't actually run a process
        mb_logger.debug(f"Creating temporary container {data_container_name}...")
        
        client.execute(
            [
                "nerdctl", "create",
                "--name", data_container_name,
                image_name,
                "/bin/true"
            ],
            safe=False
        )
        
        try:
            # Copy the content from the container to the host
            # The trailing slashes are important: they copy the contents of the path, 
            # not the path itself as a subdirectory
            mb_logger.debug(f"Copying {image_path}/ to {host_mount_path}/...")
            
            client.execute(
                [
                    "nerdctl", "cp",
                    f"{data_container_name}:{image_path}/",
                    f"{host_mount_path}/"
                ],
                safe=True
            )
            
        finally:
            # Always remove the temporary container
            mb_logger.debug(f"Removing temporary container {data_container_name}...")
            client.remove_container(data_container_name, safe=True, hide=True)
        
        # Set the permissions on the host mount path
        os.chown(host_mount_path, uid, gid)
        os.chmod(host_mount_path, int(perm, 8))
        
        mb_logger.debug(
            f"Successfully copied content from {image_name}:{image_path} "
            f"to {host_mount_path} (owner: {uid}:{gid}, perm: {perm})"
        )
        
    except Exception as e:
        mb_logger.error(f"Error copying content from image {image_name}:{image_path} to {host_mount_path}: {e}")
        raise



def realize_dir_mount_conf(
    mount_dir: str, uid: int, gid: int, perm: str
) -> None:
    """Create mount directory with specified owner and permission."""

    os.makedirs(mount_dir, exist_ok=True)
    os.chown(mount_dir, uid, gid)
    os.chmod(mount_dir, int(perm, 8))


# 对一个挂载点进行准备工作（创建目录或检查文件存在性）
def prepare_mount_entry(mount_entry: MBContainerMountEntry, image_name: str = None) -> None:
    if mount_entry.copy and image_name:
        # If copy is enabled, copy content from the image
        copy_from_image(
            image_name,
            mount_entry.target,
            mount_entry.source.real_mount_source_path,
            mount_entry.owner[0],
            mount_entry.owner[1],
            mount_entry.perm,
        )
    elif not mount_entry.file:  # 只创建目录挂载点，跳过文件挂载点。
        # 为什么要跳过？因为自动创建文件挂载点甚至只是创建它的父目录都会引起极大的困惑。
        realize_dir_mount_conf(
            mount_entry.source.real_mount_source_path,
            mount_entry.owner[0],
            mount_entry.owner[1],
            mount_entry.perm,
        )
    else:
        # 如果是文件挂载点，则检查此挂载点的实际源文件是否存在，如果不存在则报错并不要创建。
        if not os.path.exists(mount_entry.source.real_mount_source_path):
            raise FileNotFoundError(
                f"Mount source file {mount_entry.source} does not exist."
            )
        elif not os.path.isfile(mount_entry.source.real_mount_source_path):
            raise FileNotFoundError(f"Mount source {mount_entry.source} is not a file.")
