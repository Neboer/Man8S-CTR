from enum import StrEnum
import ipaddress
from typing import Optional

from mbctl.network.string_to_v6suffix import string_to_v6suffix


class DNSType(StrEnum):
    HOST = "host"
    CONTAINER = "container"
    IP_ADDRESS = "ip_address"


class MBContainerDNS:
    def __init__(self, mbcontainer_dns_str: str):
        if mbcontainer_dns_str == "host":
            self.type = DNSType.HOST
            self.value = None
        elif self._is_valid_ip_address(mbcontainer_dns_str):
            self.type = DNSType.IP_ADDRESS
            self.value = mbcontainer_dns_str
        else:
            self.type = DNSType.CONTAINER
            self.value = mbcontainer_dns_str

    def _is_valid_ip_address(self, address: str) -> bool:
        try:
            ipaddress.ip_address(address)
            return True
        except ValueError:
            return False

    def to_compose_dns_entry(self, host_yggdrasil_prefix: str) -> Optional[str]:
        if self.type == DNSType.HOST or self.value is None:
            return None
        elif self.type == DNSType.IP_ADDRESS:
            return self.value
        elif self.type == DNSType.CONTAINER:
            # Convert container name to Yggdrasil address
            return string_to_v6suffix(host_yggdrasil_prefix, self.value)

    def to_mbcontainer_dns_str(self) -> str:
        if self.type == DNSType.HOST or self.value is None:
            return "host"
        elif self.type == DNSType.IP_ADDRESS:
            return self.value
        elif self.type == DNSType.CONTAINER:
            return self.value
        else:
            raise ValueError("Invalid DNSType")
    