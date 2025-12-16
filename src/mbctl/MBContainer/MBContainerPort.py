class MBContainerPort:

    # port_map is a list of tuples (host_port, container_port)
    def __init__(self, port_map: list[tuple[int, int]]):
        self.port_map = port_map

    def to_compose_ports(self, bind_ipv6: bool = True) -> list[str]:
        result: list[str] = []
        for host, container in self.port_map:
            result.append(f"{host}:{container}")
            if bind_ipv6:
                result.append(f"[::]:{host}:{container}")
        return result

    def to_mbcontainer_port_conf(self) -> list[tuple[int, int]]:
        return self.port_map
