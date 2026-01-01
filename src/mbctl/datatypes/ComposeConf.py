# represent a docker compose file's structure.
from typing import Dict, Any, List
from msgspec import Struct, field, yaml, to_builtins
from typing import Optional


# 这不是真正的Compose文件结构，只是一个简化版，它只供mbctl程序使用，并不定义完整compose文件结构。
class ComposeServiceConf(Struct, kw_only=True, omit_defaults=True):
    image: str
    container_name: str
    hostname: str
    networks: List[str] = field(default_factory=list)
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    restart: str
    extra_hosts: Dict[str, str] = field(default_factory=dict)
    dns: Optional[str] = None


class ComposeNetworkConfig(Struct):
    external: bool = True


class ComposeConf(Struct):
    services: Dict[str, ComposeServiceConf] = field(default_factory=dict)
    networks: Dict[str, ComposeNetworkConfig] = field(default_factory=dict)
    _extra_configs: Dict[str, Any] = {}

    def to_compose_dict(self) -> Dict[str, Any]:
        """
        Convert the ComposeConf instance to a dictionary, merging extra configurations.
        """
        compose_dict: Dict[str, Any] = to_builtins(self)
        compose_service_dict: Dict = list(compose_dict["services"].values())[0]

        # 合并额外配置
        for key, value in self._extra_configs.items():
            if key in compose_service_dict and isinstance(compose_service_dict[key], dict):
                compose_service_dict[key].update(value)
            else:
                compose_service_dict[key] = value

        if "_extra_configs" in compose_dict:
            del compose_dict["_extra_configs"]

        return compose_dict

    def to_compose_yaml_str(self) -> str:
        """
        Write the ComposeConf instance to a YAML file, merging extra configurations.
        """
        compose_dict = self.to_compose_dict()
        return yaml.encode(compose_dict).decode("utf-8")
