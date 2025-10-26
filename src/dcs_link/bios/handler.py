from typing import Dict, List, Any, Callable, Optional


class IntegerParser:
    def __init__(self, mask: int, shift: int, bios_code: str):
        self.mask = mask
        self.shift = shift
        self.bios_code = bios_code
        self.current_value: Optional[int] = None

    def add_data(self, address: int, data: int):
        val = (data & self.mask) >> self.shift
        self.current_value = val


class StringParser:
    def __init__(self, address: int, length: int, bios_code: str):
        self.base_address = address
        self.length = length
        self.bios_code = bios_code
        self.buffer = bytearray(length)
        self.filled = [False] * length
        self.current_value: Optional[str] = None

    @property
    def data_ready(self) -> bool:
        return all(self.filled)

    def _set_character(self, index: int, b: int) -> bool:
        if 0 <= index < self.length:
            self.buffer[index] = b
            self.filled[index] = True
            return index + 1 == self.length
        return False

    def add_data(self, address: int, data: int):
        b1 = data & 0xFF
        b2 = (data >> 8) & 0xFF

        offset = address - self.base_address

        done = self._set_character(offset, b1)
        if not done:
            self._set_character(offset + 1, b2)

        if not self.data_ready:
            return

        new_value = bytes(self.buffer).decode('utf-8', errors='ignore')
        if new_value != self.current_value:
            self.current_value = new_value


class DataHandler:
    def __init__(self):
        self.address_lookup: Dict[int, List[Any]] = {}
        self.on_value: Optional[Callable[[str, Any], None]] = None

    def _register_integer(self, address: int, mask: int, shift: int, bios_code: str):
        parser = IntegerParser(mask, shift, bios_code)
        self.address_lookup.setdefault(address, []).append(parser)

    def _register_string(self, address: int, length: int, bios_code: str):
        parser = StringParser(address, length, bios_code)
        for i in range(length):
            self.address_lookup.setdefault(address + i, []).append(parser)

    def handle_data(self, address: int, data: int):
        parsers = self.address_lookup.get(address)
        if not parsers:
            return

        for p in parsers:
            try:
                p.add_data(address, data)
            except Exception:
                continue

            if hasattr(p, 'current_value') and isinstance(p.current_value, int):
                if self.on_value:
                    self.on_value(p.bios_code, p.current_value)

            if hasattr(p, 'data_ready') and p.data_ready:
                value = p.current_value
                if self.on_value and value is not None:
                    self.on_value(p.bios_code, value.strip('\x00 \t\n\r'))

    def update_handler(self, address_lookup: Dict[int, List[Any]]):
        self.address_lookup.clear()
        for addr, controls in address_lookup.items():
            for control in controls:
                for output in control.get('outputs', []):
                    if output.get('type') == 'integer':
                        mask = output.get('mask', 0xFFFF)
                        shift = output.get('shift_by', 0)
                        bios_code = control.get('identifier')
                        self._register_integer(addr, mask, shift, bios_code)
                    elif output.get('type') == 'string':
                        length = output.get('max_length', 1)
                        bios_code = control.get('identifier')
                        self._register_string(output.get('address', addr), length, bios_code)

    def reset(self):
        self.address_lookup.clear()
        self.on_value = None