from typing import Callable, Iterable

class ProtocolParser:
	class _State:
		AddressLow = 0
		AddressHigh = 1
		CountLow = 2
		CountHigh = 3
		DataLow = 4
		DataHigh = 5
		WaitForSync = 6

	def __init__(self, on_data_write: Callable[[int, int], None]):
		self._on_data_write = on_data_write
		self._state = ProtocolParser._State.WaitForSync
		self._sync_byte_count = 0
		self._address = 0
		self._count = 0
		self._data = 0

	def reset(self) -> None:
		self._state = ProtocolParser._State.WaitForSync
		self._sync_byte_count = 0
		self._address = 0
		self._count = 0
		self._data = 0

	def feed_bytes(self, data: Iterable[int]) -> None:
		for b in data:
			self._process_byte(b if isinstance(b, int) else ord(b))

	def _process_byte(self, b: int) -> None:
		if self._state == ProtocolParser._State.AddressLow:
			self._address = b
			self._state = ProtocolParser._State.AddressHigh
		elif self._state == ProtocolParser._State.AddressHigh:
			self._address |= (b << 8)
			if self._address == 0x5555:
				self._state = ProtocolParser._State.WaitForSync
			else:
				self._state = ProtocolParser._State.CountLow
		elif self._state == ProtocolParser._State.CountLow:
			self._count = b
			self._state = ProtocolParser._State.CountHigh
		elif self._state == ProtocolParser._State.CountHigh:
			self._count |= (b << 8)
			self._state = ProtocolParser._State.DataLow
		elif self._state == ProtocolParser._State.DataLow:
			self._data = b
			self._count -= 1
			self._state = ProtocolParser._State.DataHigh
		elif self._state == ProtocolParser._State.DataHigh:
			self._data |= (b << 8)
			self._count -= 1

			try:
				self._on_data_write(self._address, self._data)
			except Exception:
				pass

			self._address = (self._address + 2) & 0xFFFF

			self._state = ProtocolParser._State.DataLow if self._count > 0 else ProtocolParser._State.AddressLow
		elif self._state == ProtocolParser._State.WaitForSync:
			pass

		if b == 0x55:
			self._sync_byte_count += 1
		else:
			self._sync_byte_count = 0

		if self._sync_byte_count == 4:
			self._state = ProtocolParser._State.AddressLow
			self._sync_byte_count = 0