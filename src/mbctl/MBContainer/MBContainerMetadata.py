from typing import Optional

from mbctl.datatypes.MBContainerConf import MBContainerMetadataConf
from datetime import datetime


class MBContainerMetadata:
    """Metadata for MBContainer."""

    def __init__(self, metadata_conf: MBContainerMetadataConf):
        self.create_time = metadata_conf.create_time
        self.last_update_time = metadata_conf.last_update_time
        self.author = metadata_conf.author

    def to_mbcontainer_metadata_conf(self) -> MBContainerMetadataConf:
        """Convert back to MBContainerMetadataConf."""
        return MBContainerMetadataConf(
            create_time=self.create_time,
            last_update_time=self.last_update_time,
            author=self.author,
        )

    def update_last_update_time_to_now(self):
        """Update the last_update_time to current time."""

        self.last_update_time = datetime.now()
