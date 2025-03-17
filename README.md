[中文文档](README_zh.md)

# IBKR Event Daemon

A flexible event-driven daemon for Interactive Brokers TWS/Gateway that handles real-time market data and trading events.

## Features

- Event-driven architecture for handling IBKR market data and trading events
- Simple handler pattern for implementing custom event processors
- Built-in support for real-time bar data
- Configurable via environment variables or command-line options
- Comprehensive logging with rotation and retention policies
- Supervisor integration for process management

## Installation

```bash
pip install ibkr-event-daemon
```

## Quick Start

1. Configure your environment variables in `.env`:
```
IB_EVENT_DAEMON_HOST=127.0.0.1
IB_EVENT_DAEMON_PORT=7497
IB_EVENT_DAEMON_CLIENTID=1
IB_EVENT_DAEMON_TIMEOUT=4
IB_EVENT_DAEMON_READONLY=False
IB_EVENT_DAEMON_ACCOUNT=
IB_EVENT_DAEMON_RAISESYNCERRORS=False
IB_EVENT_DAEMON_SETUP_PATHS="./example"
```

2. Start the daemon:
```bash
ibkr-daemon start
```

Or with custom logging:
```bash
ibkr-daemon start --log-level DEBUG --log-file logs/daemon.log
```

## Creating Custom Handlers

Handlers are Python modules that process IBKR events. Place your handlers in the directory specified by `IB_EVENT_DAEMON_SETUP_PATHS`.

Example handler for real-time bar data (`example/realtimebar_example.py`):

```python
from ib_async import IB, Forex
from ibkr_event_daemon.core import LoggerType

def setup(ib: IB, logger: LoggerType) -> None:
    usd_jpy = Forex('USDJPY')
    bars = ib.reqRealTimeBars(
        usd_jpy, 
        barSize=5, 
        whatToShow="MIDPOINT", 
        useRTH=True
    )
    bars.updateEvent += onBarUpdate

def onBarUpdate(bars, hasNewBar):
    if hasNewBar:
        print(bars[-1])
```

## Configuration

Configuration can be managed through:
- Environment variables (`.env` file)
- Command-line options
- Configuration commands

Show current configuration:
```bash
ibkr-daemon config show
```

Initialize default configuration:
```bash
ibkr-daemon config init
```

## Process Management

The project includes a `supervisord.conf` for process management. This allows for:
- Automatic restart on failure
- Process monitoring
- Log management

## Development

To run in development mode:

1. Clone the repository
2. Install dependencies:
```bash
pip install -e .
```
3. Create and configure `.env` file:
```bash
ibkr-daemon config init
```
4. Start the daemon:
```bash
python -m ibkr_event_daemon start
```

## License

[MIT License](LICENSE)