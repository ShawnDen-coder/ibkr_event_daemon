"""Constants module for the IBKR event daemon.

This module contains constant values used throughout the IBKR event daemon.

Example:
    >>> from ibkr_event_daemon.constants import ENV_PREFIX
    >>> env_var = f"{ENV_PREFIX}HOST"  # Creates 'IB_EVENT_DAEMON_HOST'
    >>> print(f"Looking for environment variable: {env_var}")
"""

ENV_PREFIX = "IB_EVENT_DAEMON_"
