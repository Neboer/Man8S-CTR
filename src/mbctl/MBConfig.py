from msgspec import Struct, field, yaml
from os import path

MAN8S_CONFIG_FILE = "/etc/mbctl/config.yaml"


class MBNetworkNameConfig(Struct):
    noygg = "man8br"
    withygg = "man8yggbr"


class MBConfig(Struct):
    storage_path: str = "/var/lib/man8s"
    network: MBNetworkNameConfig = field(default_factory=MBNetworkNameConfig)


if path.exists(MAN8S_CONFIG_FILE):
    with open(MAN8S_CONFIG_FILE, "r") as f:
        config_data = f.read()
    mb_config: MBConfig = yaml.decode(config_data, type=MBConfig)
else:
    mb_config: MBConfig = MBConfig()
  