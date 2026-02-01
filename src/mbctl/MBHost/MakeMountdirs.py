import os
from mbctl.MBContainer.MBContainerMount import MBContainerMountEntry


def realize_dir_mount_conf(
    mount_dir: str, uid: int = 0, gid: int = 0, perm: str = "755"
) -> None:
    """Create mount directory with specified owner and permission."""

    os.makedirs(mount_dir, exist_ok=True)
    os.chown(mount_dir, uid, gid)
    os.chmod(mount_dir, int(perm, 8))


# 对一个挂载点进行准备工作（创建目录或检查文件存在性）
def prepare_mount_entry(mount_entry: MBContainerMountEntry) -> None:
    if not mount_entry.file:  # 只创建目录挂载点，跳过文件挂载点。
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
