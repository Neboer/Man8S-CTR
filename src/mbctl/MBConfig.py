import posixpath

import yaml
from pydantic import BaseModel, ConfigDict, Field

MAN8S_CONFIG_FILE = "/etc/mbctl/config.yaml"


class MBNetworkNameConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    noygg: str = "man8br"
    withygg: str = "man8yggbr"


class NerdConfig(BaseModel):
    # These nerdconfig values are passed when invoking nerdctl.
    model_config = ConfigDict(extra="forbid")

    # mbctl 只针对固定的 namespace 和 snapshotter 进行配置，这个配置没有什么用，应该在nerdctl的配置文件中设置。
    namespace: str = "man8s.io"
    snapshotter: str = "btrfs"


class MBConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_path: str = "/var/lib/man8s"
    network_name: MBNetworkNameConfig = Field(default_factory=MBNetworkNameConfig)
    config_file: str = "container.yaml"
    nerdconfig: NerdConfig = Field(default_factory=NerdConfig)
    local_domain: str = "man8s.local"

    yggaddr: str  # 至少，需要把这个设置了。


def _load_mb_config() -> MBConfig:
    if posixpath.exists(MAN8S_CONFIG_FILE):
        with open(MAN8S_CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
        return MBConfig.model_validate(config_data)
    else:
        raise FileNotFoundError(f"MBConfig file not found at {MAN8S_CONFIG_FILE}")


mb_config: MBConfig = _load_mb_config()
