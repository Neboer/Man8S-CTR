import ipaddress
from .string_to_v6suffix import string_to_v6suffix


def get_ipv6_addr_prefix(addr: str, prefix_len: int = 64) -> str:
    """从完整的IPv6地址中提取前缀部分。"""
    network = ipaddress.IPv6Network(f"{addr}/{prefix_len}", strict=False)
    return str(network.network_address) + f"/{prefix_len}"
