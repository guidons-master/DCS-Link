# DCS-Link

[![PyPI version](https://badge.fury.io/py/dcs-link.svg)](https://badge.fury.io/py/dcs-link)
[![Python Version](https://img.shields.io/pypi/pyversions/dcs-link.svg)](https://pypi.org/project/dcs-link/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, high-performance Python library for connecting to DCS-BIOS and DCS-INSIGHT in DCS World.

## Features

- **Asynchronous**: Built with asyncio for non-blocking operations
- **Lightweight**: Minimal overhead and memory footprint
- **Easy to use**: Simple API for connecting and listening to DCS data
- **Event-driven**: Register callbacks for specific controls or values

## Installation

First, make sure you have Python 3.8 or higher installed.

Install dcs-link using pip:

```bash
pip install dcs_link
```

Or install in development mode:

```bash
pip install -e .
```

### Prerequisites

To use this library, you need:

1. DCS World installed
2. DCS-BIOS installed and configured
   - Download from: https://github.com/DCS-Skunkworks/dcs-bios
   - Follow installation instructions in the DCS-BIOS documentation
3. DCS-INSIGHT installed and configured (for advanced API calls)
   - Download from: https://github.com/DCS-Skunkworks/DCS-INSIGHT
   - Follow installation instructions in the DCS-INSIGHT documentation

## Quick Start

Check the [examples](examples/) directory for usage examples:

- [Basic example](examples/test.py) - Shows basic usage with both DCS-BIOS and DCS-INSIGHT

## API Reference

### DCSLink

Main class for interacting with DCS-BIOS and DCS-INSIGHT.

#### Constructor

```python
bios, insight = DCSLink(config: Optional[LinkConfig] = None)
```

Returns a tuple containing BiosClient and InsightClient instances.

### BiosClient

Client for interacting with DCS-BIOS.

#### Methods

- `connect(timeout: Optional[float] = None)` - Connect to DCS-BIOS
- `on(event_name: str, handler: Callable)` - Register listener for control changes
- `off(event_name: str)` - Remove listener
- `send(command: str)` - Send command to DCS
- `close()` - Close connection

#### Properties

- `aircraft_name` - Current aircraft name
- `events` - Set of all available events for the current aircraft

### InsightClient

Client for interacting with DCS-INSIGHT.

#### Methods

- `connect(timeout: Optional[float] = None)` - Connect to DCS-INSIGHT
- `call(command: str, timeout: float = 5.0, **kwargs)` - Call DCS-INSIGHT API function
- `close()` - Close connection

#### Properties

- `apis` - Set of all available API functions

### LinkConfig

Configuration class for DCSLink.

```python
config = LinkConfig(
    json_dir="",            # Path to DCS-BIOS JSON files (auto-detected if empty)
    log_enable=True,        # Enable logging
    log_level=20,           # Logging level (default is INFO)
    network=NetworkConfig() # Network configuration
)
```

### NetworkConfig

Network configuration for DCS-BIOS and DCS-INSIGHT connections.

```python
network_config = NetworkConfig(
    server_ip='127.0.0.1',         # Server IP address
    multicast_group='239.255.50.10', # Multicast group IP
    loopback_interface="",         # Loopback interface
    receive_port=5010,             # Port to receive data from DCS-BIOS
    send_port=7778,                # Port to send commands to DCS-BIOS
    call_port=7790                 # Port for DCS-INSIGHT API calls
)
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.