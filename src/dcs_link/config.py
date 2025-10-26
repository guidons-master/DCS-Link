
from dataclasses import dataclass
from typing import Optional

@dataclass
class NetworkConfig:    
    server_ip: str = "127.0.0.1"
    multicast_group: str = '239.255.50.10'
    loopback_interface: str = ""
    receive_port: int = 5010
    send_port: int = 7778
    call_port: int = 7790  # for insight

@dataclass
class LinkConfig:    
    json_dir: str = ""
    log_enable: bool = True
    log_level: int = 20  # INFO level
    network: NetworkConfig = NetworkConfig()