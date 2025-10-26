from .config import LinkConfig
from .bios.client import BiosClient
from .insight.client import InsightClient
from typing import Optional

__all__ = [ "DCSLink", "LinkConfig" ]

class DCSLink(tuple):
    """
        DCSLink is a tuple of two clients: BIOS and INSIGHT.
    """
    def __new__(cls, config: Optional[LinkConfig] = None):
        config = config or LinkConfig()
        return super().__new__(cls, ( BiosClient(config), InsightClient(config)))