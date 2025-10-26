import asyncio
import socket
import struct
from typing import Optional, Dict, Any, Callable, Set, Tuple
from pathlib import Path
from platform import system

from ..config import LinkConfig
from ..logger import Logger
from .protocol import ProtocolParser
from .handler import DataHandler
from .loader import JsonLoader

class BiosClient:    
    def __init__(self, config: LinkConfig):
        self._config = config
        self._logger = Logger(self.__class__.__name__, self._config.log_level if self._config.log_enable else 50)

        self._json_dir = self._config.json_dir or self._find_json()
        if not self._json_dir:
            raise FileNotFoundError("Could not find DCS-BIOS JSON directory")
        
        self._listen_sock: Optional[socket.socket] = None
        self._send_sock: Optional[socket.socket] = None
        self._received: asyncio.Event = asyncio.Event()
        self._running = False
        
        self._loader = JsonLoader(self._json_dir)
        self._data_handler = DataHandler()
        self._data_handler.update_handler(self._loader.address_lookup)

        self._event_handlers: Dict[str, Callable] = {}
        self._data_handler.on_value = self._on_value_from_handler
        self._protocol_parser = ProtocolParser(self._data_handler.handle_data)
        
        self.aircraft_name: Optional[str] = None
        self._events_cache: Optional[Set[str]] = None
        
        self._logger.info("Waiting for Connection")

    def _find_json(self) -> str:
        self._logger.debug("Searching for DCS-BIOS JSON directory")
        if system() == "Windows": 
            for folder in ("DCS", "DCS.openbeta"):
                json_dir = Path.home() / "Saved Games" / folder / "Scripts" / "DCS-BIOS" / "doc" / "json"
                if json_dir.is_dir():
                    return str(json_dir)

        return ""
                
    async def connect(self, timeout: Optional[float] = None) -> bool:
        """Establish connection to DCS-BIOS.
        
        Args:
            timeout: Time to wait for connection before considering connection failed, None for no timeout
        """
        self._listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listen_sock.bind((self._config.network.loopback_interface, self._config.network.receive_port))

        mreq = struct.pack('4sl', socket.inet_aton(self._config.network.multicast_group), socket.INADDR_ANY)
        self._listen_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        self._running = True
        asyncio.create_task(self._listen_loop())
        
        try:
            await asyncio.wait_for(self._received.wait(), timeout)            
            self._loader.load_aircraft(self.aircraft_name)
            self._data_handler.update_handler(self._loader.address_lookup)
            self._logger.info(f"Connected to DCS-BIOS")
            return True
        except asyncio.TimeoutError:
            self._logger.error("Connected to DCS-BIOS timeout")
            self.close()
            return False
            
    async def _listen_loop(self):
        self._logger.debug("Starting listen loop")
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                data = await loop.sock_recv(self._listen_sock, 65536)
                self._protocol_parser.feed_bytes(data)
            except Exception as e:
                if self._running:
                    self._logger.error(f"Error in listen loop: {e}")
                break

    def on(self, event_name: str, handler: Callable):
        """Register an event handler.
        
        Args:
            event_name: Name of the event to listen for
            handler: Function to call when event is emitted
        """
        if event_name not in self.events:
            self._logger.warning(f"Event '{event_name}' is not supported")

        self._event_handlers[event_name] = handler
        self._logger.debug(f"Registered handler for event: {event_name}")

    def off(self, event_name: str):
        """Unregister an event handler.
        
        Args:
            event_name: Name of the event to unregister
        """
        if event_name in self.events and event_name in self._event_handlers:
            self._event_handlers.pop(event_name)

    def send(self, command: str):
        """Send a command to DCS-BIOS.
        
        Args:
            command: Command string to send
        """
        if self._send_sock:
            self._send_sock.sendto(
                command.encode('utf-8'), 
                (self._config.network.server_ip , self._config.network.send_port)
            )
            self._logger.debug(f"Sent command: {command}")

    @property
    def events(self) -> Set[str]:
        """
            Returns a set of all events that can be emitted.
        """
        if self._events_cache is not None:
            return self._events_cache
            
        event_set = set(['MISSION_ENDED',])
        
        for controls_list in self._loader.address_lookup.values():
            for control in controls_list:
                if 'identifier' in control and control['identifier'] != "_ACFT_NAME":
                    event_set.add(control['identifier'])
        
        self._events_cache = event_set
        return event_set

    def _on_value_from_handler(self, bios_code: str, value: Any):
        if bios_code == "_ACFT_NAME":
            if not self.aircraft_name:
                self.aircraft_name = value
            elif value == "":
                if "MISSION_ENDED" in self._event_handlers:
                    try:
                        self._event_handlers["MISSION_ENDED"](None)
                    except Exception:
                        self._logger.error(f" Error in event MISSION_ENDED: {h.__name__}")
                
                self.close()
            
            if not self._received.is_set(): 
                self._received.set()
            
            return
        
        if bios_code in self._event_handlers:
            try:
                self._event_handlers[bios_code](value)
            except Exception:
                self._logger.error(f" Error in event {bios_code}: {h.__name__}")

    def close(self):
        """
            Close the connection.
        """
        self._logger.info("Closing connection")
        self._running = False
        if self._listen_sock:
            self._listen_sock.close()
            self._listen_sock = None

        if self._send_sock:
            self._send_sock.close()
            self._send_sock = None
    
        self._protocol_parser.reset()
        self._data_handler.reset()