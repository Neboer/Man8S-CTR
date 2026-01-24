# represent a docker compose file's structure.
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from mbctl.MBLog import mb_logger

# This is a simplified Compose file structure for mbctl only.
class ComposeServiceConf(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: str
    container_name: str
    hostname: str
    networks: List[str] = Field(default_factory=list)
    ports: List[str] = Field(default_factory=list)
    volumes: List[str] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    restart: str
    extra_hosts: Dict[str, str] = Field(default_factory=dict)
    dns: Optional[str] = None


class ComposeNetworkConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external: bool


class ComposeConf(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    services: Dict[str, ComposeServiceConf] = Field(default_factory=dict)
    networks: Dict[str, ComposeNetworkConfig] = Field(default_factory=dict)
    _extra_configs: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, extra_compose_configs={}, **data):
        # Call the parent's __init__ first
        # Extract extra compose configurations if provided
        super().__init__(**data)
        self._extra_configs = extra_compose_configs

    def to_compose_dict(self) -> Dict[str, Any]:
        """Convert the ComposeConf instance to a dictionary, merging extra configurations."""
        compose_dict: Dict[str, Any] = self.model_dump(
            mode="python", by_alias=True, exclude_defaults=True
        )

        services = compose_dict.get("services", {})
        compose_service_dict: Dict[str, Any]

        if services:
            compose_service_dict = list(services.values())[0]
        else:
            compose_service_dict = {}

        for key, value in self._extra_configs.items():
            if key in compose_service_dict:
                mb_logger.warning(
                    f"Overriding existing key '{key}' in compose service with extra configuration."
                )
            compose_service_dict[key] = value

        if compose_service_dict and services:
            first_service_key = list(services.keys())[0]
            services[first_service_key] = compose_service_dict

        return compose_dict

    def to_compose_yaml_str(self) -> str:
        """Serialize the ComposeConf instance to a YAML string."""
        compose_dict = self.to_compose_dict()
        return yaml.safe_dump(compose_dict, sort_keys=False)
