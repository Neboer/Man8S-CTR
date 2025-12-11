from mbctl.type_conv import convert_full_conf
from mbctl.datatypes import ComposeConf, MBContainerConf
from msgspec import yaml
from os import path

current_dir = path.dirname(__file__)

def test_conf_convert():
    with open(path.join(current_dir, "resources/test-man8s-conf.yaml"), "r", encoding="utf8") as test_conf_file:
        test_conf_content = test_conf_file.read()

    test_mbcontainer_conf = yaml.decode(test_conf_content, type=MBContainerConf)
    output_compose_conf = convert_full_conf(test_mbcontainer_conf, "test_container")

    with open(path.join(current_dir, "resources/test-man8s-compose.yaml"), "wb") as output_compose_file:
        output_compose_file.write(yaml.encode(output_compose_conf))
