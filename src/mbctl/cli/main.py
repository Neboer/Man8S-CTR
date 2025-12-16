import os
from typing import Annotated
import typer
from mbctl.MBHost import MBHost
from prettytable import PrettyTable, TableStyle
from mbctl.MBContainer import MBContainer
from mbctl.datatypes import MBContainerConf, MBContainerMetadataConf

app = typer.Typer()
host = MBHost()


@app.command()
def build(container_name: str):
    print(f"Building container: {container_name}")
    host.build_new_container(container_name)


@app.command()
def prune(container_name: str):
    print(f"Pruning container: {container_name}")
    host.remove_container_mounts(container_name)


@app.command()
def prepare(
    container_name: str,
    image: Annotated[str, typer.Option(prompt="Please input a image.")],
    enable_ygg: Annotated[bool, typer.Option(prompt="Enable Yggdrasil?")] = True,
    autostart: Annotated[bool, typer.Option(prompt="Enable AutoStart?")] = True,
    author: Annotated[
        str, typer.Option(prompt="Please input author metadata.")
    ] = "unknown",
):
    print(f"preparing container: {container_name}")
    container_conf_metadata = MBContainerMetadataConf(author=author)
    container_conf = MBContainerConf(
        image=image,
        enable_ygg=enable_ygg,
        autostart=autostart,
        metadata=container_conf_metadata,
    )
    host.create_container_from_conf(container_name, container_conf)


@app.command()
def recreate(container_name: str):
    print(f"Recreating container: {container_name}")
    host.client.force_delete_container(container_name)
    host.build_new_container(container_name)


@app.command()
def start_all_autostart():
    containers = host.list_containers()
    for container in containers:
        if container.autostart:
            print(f"Starting container: {container.name}")
            host.client.start_container(container.name)


@app.command()
def list():
    # 列出所有的容器，并整理他们的状态，打印他们的名字、镜像、运行状态以及ygg地址。
    table = PrettyTable()
    table.field_names = ["Container", "Image", "Status", "AutoStart", "YggAddr"]

    table.add_rows(
        [
            [
                container.name,
                container.image,
                container.status.value,
                "Yes" if container.autostart else "No",
                container.yggdrasil_addr,
            ]
            for container in host.list_containers()
        ]
    )
    table.set_style(TableStyle.PLAIN_COLUMNS)
    print(table)


if __name__ == "__main__":
    app()
