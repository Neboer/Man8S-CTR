from enum import Enum


class MountType(Enum):
    data = "data"
    log = "log"
    conf = "conf"
    cache = "cache"
    plugin = "plugin"
