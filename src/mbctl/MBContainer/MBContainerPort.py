from typing import Sequence, Tuple
from mbctl.datatypes import MBPortPiece


class MBContainerPortMapRule:
    def __init__(self, host_port: int, container_port: int, udp: bool = False):
        self.host_port = host_port
        self.container_port = container_port
        self.udp = udp
        self.tcp = not udp

    def to_compose_portmaps(self) -> list[str]:
        port_str = f"{self.host_port}:{self.container_port}"
        if self.udp:
            port_str += "/udp"
        ipv6_port_str = f"[::]:{port_str}"
        return [port_str, ipv6_port_str]

    def to_mbcontainer_port_conf(self) -> MBPortPiece:
        if self.udp:
            return (self.host_port, self.container_port, self.udp)
        else:
            return (self.host_port, self.container_port)


class MBContainerPortMap:

    # port_map is a list of tuples (host_port, container_port, is_udp)
    def __init__(self, port_map: Sequence[MBPortPiece]):
        self.port_map: list[MBContainerPortMapRule] = [
            MBContainerPortMapRule(
                host_port=entry[0],
                container_port=entry[1],
                udp=entry[2] if len(entry) == 3 else False,
            )
            for entry in port_map
        ]

    def to_compose_ports(self, bind_ipv6: bool = True) -> list[str]:
        ports: list[str] = []
        for rule in self.port_map:
            ports.extend(rule.to_compose_portmaps())
        return ports

    def to_mbcontainer_port_conf(self) -> list[MBPortPiece]:
        return [rule.to_mbcontainer_port_conf() for rule in self.port_map]
