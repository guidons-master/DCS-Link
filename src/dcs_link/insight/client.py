import asyncio
import json
import socket
from typing import Optional, Any
from ..config import LinkConfig
from ..logger import Logger

class InsightClient:
    def __init__(self, config: LinkConfig):
        self._config = config
        self._logger = Logger(self.__class__.__name__, self._config.log_level if self._config.log_enable else 50)

        self._call_sock: Optional[socket.socket] = None
        self._received = asyncio.Event()
        self._running = False
        self._buffer = ""
        self._apis: dict[str, dict] = {}
        self._response: Any = None

        self._logger.info("Waiting for Connection")

    async def connect(self, timeout: Optional[float] = None) -> bool:
        """Establish connection to DCS-INSIGHT.
        
        Args:
            timeout: Time to wait for connection before considering connection failed, None for no timeout
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._config.network.server_ip, self._config.network.call_port))
        self._call_sock = sock
        self._running = True

        asyncio.create_task(self._listen_loop())
        sock.send(b"SENDAPI\n")

        try:
            await asyncio.wait_for(self._received.wait(), timeout)
            self._received.clear()
            self._logger.info("Connected to DCS-INSIGHT")
            return True
        except asyncio.TimeoutError:
            self._logger.error("Connection to DCS-INSIGHT timed out")
            self.close()
            return False

    async def call(self, command: str, timeout: float = 5.0, **kwargs) -> Optional[str]:
        """Call an API.
        
        Args:
            command: The name of the API to call.
            timeout: The timeout for response.
            **kwargs: The parameters to pass to the API.
        """
        if not self._running or self._call_sock is None:
            self._logger.error("Not connected. Call connect() first.")
            return None

        api_def = self._apis.get(command)
        if not api_def:
            self._logger.error(f"API not found: {command}")
            return None

        param_defs = api_def["parameter_defs"]
        expected = {p["name"] for p in param_defs}
        provided = set(kwargs)

        if provided != expected:
            msg = f"Parameter mismatch for {command}."
            if missing := expected - provided:
                msg += f" Missing: {missing}."
            if extra := provided - expected:
                msg += f" Unexpected: {extra}."
            self._logger.error(msg)
            return None

        call_obj = {
            **api_def,
            "parameter_defs": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "value": str(kwargs[p["name"]]),
                    "type": p["type"]
                }
                for p in param_defs
            ]
        }

        payload = (json.dumps(call_obj, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            self._call_sock.send(payload)
        except OSError as e:
            self._logger.error(f"Send failed: {e}")
            return None

        if not api_def.get("returns_data", False):
            return None

        try:
            await asyncio.wait_for(self._received.wait(), timeout)
            self._received.clear()
            return self._response
        except asyncio.TimeoutError:
            self._logger.warning(f"Call to {command} timed out")
            return None

    @property
    def apis(self) -> set[str]:
        """
            Returns a set of available APIs.
        """
        return set(self._apis.keys())

    async def _listen_loop(self):
        self._logger.debug("Starting listen loop")
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                data = await loop.sock_recv(self._call_sock, 65536)
                if not data:
                    break
                self._process_buffer(data)
            except Exception as e:
                if self._running:
                    self._logger.error(f"Listen loop error: {e}")
                break

    def _process_buffer(self, data: bytes):
        self._buffer += data.decode('utf-8')
        while self._buffer.strip():
            try:
                obj, end = json.JSONDecoder().raw_decode(self._buffer)
                self._buffer = self._buffer[end:].lstrip()

                if isinstance(obj, list):
                    self._apis = {d["api_syntax"]: d for d in obj}
                    self._received.set()
                elif isinstance(obj, dict):
                    self._response = obj.get("result")
                    self._received.set()
            except json.JSONDecodeError:
                break  # Incomplete message, wait for more data

    def close(self):
        """
            Close the connection.
        """
        self._logger.info("Closing connection")
        self._running = False
        if self._call_sock:
            self._call_sock.close()
            self._call_sock = None