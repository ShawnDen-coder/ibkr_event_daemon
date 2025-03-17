"""Configuration module for the IBKR event daemon.

This module provides configuration settings for connecting to Interactive Brokers TWS/Gateway
using pydantic for validation and environment variable support.

Example:
    >>> # Create settings from environment variables
    >>> settings = IbkrSettings()
    >>> # Create settings with custom values
    >>> settings = IbkrSettings(
    ...     host='127.0.0.1',
    ...     port=4002,  # Paper trading port
    ...     clientid=12
    ... )
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing_extensions import Optional

from ibkr_event_daemon.constants import ENV_PREFIX


class IbkrSettings(BaseSettings):
    """Configuration settings for IBKR connection and client.

    This class uses pydantic BaseSettings to manage configuration through environment
    variables with the prefix defined in constants.ENV_PREFIX. Settings can be loaded from a .env file.

    Attributes:
        host: The IBKR TWS/Gateway host address. Defaults to '127.0.0.1'.
        port: The IBKR TWS/Gateway port number. Defaults to 7497.
        clientid: The client ID for IBKR connection. Defaults to 1.
        timeout: Connection timeout in seconds. Defaults to 4.
        readonly: Whether to connect in read-only mode. Defaults to False.
        account: IBKR account identifier. Defaults to empty string.
        raisesyncerrors: Whether to raise sync errors. Defaults to False.
        setup_paths: Optional paths for setup configuration. Defaults to None.

    Example:
        >>> # Load from environment variables
        >>> settings = IbkrSettings()
        >>> # Create with custom values
        >>> settings = IbkrSettings(
        ...     host='localhost',
        ...     port=4001,
        ...     clientid=123,
        ...     readonly=True
        ... )
        >>> # Access settings
        >>> print(f"Connecting to {settings.host}:{settings.port}")
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix=ENV_PREFIX,
    )

    host: str = Field(default="127.0.0.1", validation_alias=f"{ENV_PREFIX}host", alias="host")
    port: int = Field(default=7497, validation_alias=f"{ENV_PREFIX}port", alias="port")
    clientid: int = Field(default=1, validation_alias=f"{ENV_PREFIX}clientid", alias="clientId")
    timeout: int = Field(default=4, validation_alias=f"{ENV_PREFIX}timeout", alias="timeout")
    readonly: bool = Field(default=False, validation_alias=f"{ENV_PREFIX}readonly", alias="readonly")
    account: str = Field(default="", validation_alias=f"{ENV_PREFIX}account", alias="account")
    raisesyncerrors: bool = Field(default=False, validation_alias=f"{ENV_PREFIX}raisesyncerrors", alias="raiseSyncErrors")

    setup_paths: Optional[str] = Field(default=None, validation_alias=f"{ENV_PREFIX}setup_paths", alias="setup_paths")
