from pathlib import Path

from mbctl.MBHost import MBHost
from mbctl.datatypes import (
    MBContainerConf,
    MBContainerMountConf,
    MBContainerMountPointConf,
    MountType,
)
from mbctl.MBConfig import mb_config
from mbctl.MBHost.NerdClient.NerdContainer import NerdContainerState


class FakeNerdClient:
    def get_container_state(self, container_name: str) -> NerdContainerState:
        return NerdContainerState.not_exist


def _write_conf(base_dir: Path, name: str, conf: MBContainerConf) -> None:
    conf_dir = base_dir / MountType.conf.value / name
    conf_dir.mkdir(parents=True, exist_ok=True)
    conf_path = conf_dir / mb_config.config_file
    conf.to_yaml_file(conf_path.as_posix())


def test_mbhost_resolves_dependencies(tmp_path, monkeypatch):
    # isolate storage under tmp and write two dependent container configs
    monkeypatch.setattr(mb_config, "storage_path", tmp_path.as_posix())

    base_conf = MBContainerConf(
        image="example/base:latest",
        require=[],
        mount=MBContainerMountConf(
            data={"/data": MBContainerMountPointConf()},
        ),
    )
    child_conf = MBContainerConf(
        image="example/child:latest",
        require=["base"],
        mount=MBContainerMountConf(
            data={"/frombase": MBContainerMountPointConf(source="base:/data")},
        ),
    )

    _write_conf(tmp_path, "base", base_conf)
    _write_conf(tmp_path, "child", child_conf)

    host = MBHost(client=FakeNerdClient(), yggaddr="ygg", yggprefix="2001:db8::/64") # type: ignore

    assert set(host.list_all_mbcontainer_names()) == {"base", "child"}
    assert {c.name for c in host.list_containers()} == {"base", "child"}

    base = host.get_mbcontainer("base")
    child = host.get_mbcontainer("child")

    base_mount = next(e for e in base.mount.mount_points if e.target == "/data")
    child_mount = next(e for e in child.mount.mount_points if e.target == "/frombase")

    assert child_mount.source.real_mount_source == base_mount.source.real_mount_source
    assert child.resolved
