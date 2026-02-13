import ipaddress
from .string_to_v6suffix import string_to_v6suffix


# 从一个ygg地址中得到一个可路由的ygg网段。
def get_ipv6_addr_prefix(addr: str, prefix_len: int = 64) -> str:
    """从完整的IPv6地址中提取前缀部分。如果输入为200开头，则会被转换成300"""
    network = ipaddress.IPv6Network(f"{addr}/{prefix_len}", strict=False)
    result_str = str(network.network_address)
    result_str = '3' + result_str[1:]  # 将200开头改为300开头
    return result_str + f"/{prefix_len}"
