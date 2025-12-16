# represent a docker compose file's structure.
from typing import Dict, Any, List
from msgspec import Struct, field
from msgspec import yaml


class ComposeServiceConf(Struct, kw_only=True):
    image: str
    container_name: str
    hostname: str
    networks: List[str] = field(default_factory=list)
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    restart: str


class ComposeNetworkConfig(Struct):
    external: bool = True


class ComposeConf(Struct):
    services: Dict[str, ComposeServiceConf] = field(default_factory=dict)
    networks: Dict[str, ComposeNetworkConfig] = field(default_factory=dict)

    def to_yaml_file(self, compose_conf: "ComposeConf", file_path: str) -> None:

        with open(file_path, "w", encoding="utf-8") as f:
            yaml_data = yaml.encode(compose_conf)
            f.write(yaml_data.decode("utf-8"))
