from msgspec import Struct, field, yaml
import posixpath

MAN8S_CONFIG_FILE = "/etc/mbctl/config.yaml"


class MBNetworkNameConfig(Struct):
    noygg = "man8br"
    withygg = "man8yggbr"

# 这些nerdconfig会在执行nerdctl命令时传递给它们。
class NerdConfig(Struct):
    namespace: str = "man8s.io"
    snapshotter: str = "btrfs"


class MBConfig(Struct):
    storage_path: str = "/var/lib/man8s"
    network: MBNetworkNameConfig = field(default_factory=MBNetworkNameConfig)
    config_file: str = "container.yaml"
    nerdconfig: NerdConfig = field(default_factory=NerdConfig)
    local_domain: str = "man8s.local"

if posixpath.exists(MAN8S_CONFIG_FILE):
    with open(MAN8S_CONFIG_FILE, "r") as f:
        config_data = f.read()
    mb_config: MBConfig = yaml.decode(config_data, type=MBConfig)
else:
    mb_config: MBConfig = MBConfig()
