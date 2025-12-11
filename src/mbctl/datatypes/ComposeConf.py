# represent a docker compose file's structure.
from typing import Dict, Any, List
from msgspec import Struct, field

class ComposeServiceConf(Struct):
    image: str
    container_name: str
    hostname: str
    networks: List[str] = []
    ports: List[str] = []
    volumes: List[str] = []
    environment: Dict[str, str] = {}


class ComposeNetworkConfig(Struct):
    external: bool = True


class ComposeConf(Struct):
    services: Dict[str, ComposeServiceConf] = {}
    networks: Dict[str, ComposeNetworkConfig] = {}
