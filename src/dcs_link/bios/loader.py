import json
import os
from typing import Dict, Any, List

class JsonLoader:
    PRELOAD_FILES = (
        "AircraftAliases.json",
        "MetadataStart.json",
        "MetadataEnd.json"
    )
    
    def __init__(self, json_dir: str):
        self.json_dir = json_dir
        self.address_lookup: Dict[int, List[Any]] = {}
        self._preload_files()

    def _preload_files(self) -> None:
        aliases_path = os.path.join(self.json_dir, self.PRELOAD_FILES[0])
        
        with open(aliases_path, 'r', encoding='utf-8') as f:
            self._aliases = json.load(f)

        for filename in self.PRELOAD_FILES[1:]:
            filepath = os.path.join(self.json_dir, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._parse_aircraft_controls(data)

    def load_aircraft(self, aircraft_name: str) -> None:                
        for filename in self._aliases[aircraft_name if aircraft_name in self._aliases else ""]:
            filepath = os.path.join(self.json_dir, f'{filename}.json')
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._parse_aircraft_controls(data)
                
    def _parse_aircraft_controls(self, json_data: Dict[str, Any]) -> None:
        for category in json_data.values():
            if not isinstance(category, dict):
                continue
                
            for control in category.values():
                if not isinstance(control, dict) or 'identifier' not in control:
                    continue

                for output in control.get('outputs', []):
                    address = output['address']
                    if address not in self.address_lookup:
                        self.address_lookup[address] = []
                    # Avoid duplicate entries
                    if control not in self.address_lookup[address]:
                        self.address_lookup[address].append(control)