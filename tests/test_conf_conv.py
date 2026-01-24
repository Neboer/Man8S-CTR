from mbctl.datatypes import ComposeConf, MBContainerConf
from mbctl.MBContainer import MBContainer
from os import path
from mbctl.MBHost import MBHost

current_dir = path.dirname(__file__)

def test_conf_convert():
    test_mbcontainer_conf = MBContainerConf.from_yaml_file(
        path.join(current_dir, "resources/test-man8s-conf.yaml")
    )

    test_container = MBContainer(
        "test_container", test_mbcontainer_conf, "300:6b9f:cca2:a583::/64"
    )

    output_compose_conf = test_container.to_compose_conf()

    with open(
        path.join(current_dir, "resources/test-man8s-compose.yaml"), "w"
    ) as output_compose_file:
        output_compose_file.write(output_compose_conf.to_compose_yaml_str())

    MBContainerConf.to_json_schema_file(
        path.join(current_dir, "resources/mbcontainerconf-schema.json")
    )


def test_container_list():
    host = MBHost(yggaddr="200:64f7:cae4:9395:44f1:455d:de99:e7", yggprefix="300:64f7:cae4:9395::/64")
    host.list_all_mbcontainer_names()

