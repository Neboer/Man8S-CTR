
def convert_port_conf(
    port_conf: list[tuple[int, int]],
) -> list[str]:
    result = []
    for host, container in port_conf:
        result.append(f"{host}:{container}")
        result.append(f"[::]:{host}:{container}") # add IPv6 mapping

    return result
