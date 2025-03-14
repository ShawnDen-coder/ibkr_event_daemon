"""Configuration module for the IBKR Event Daemon.

This module provides configuration management for:
1. IB connection settings
2. Daemon operation parameters
3. Logging configuration
4. Handler behavior settings

Example:
    # Load configuration from environment variables
    config = Config()
    
    # Connect to IB
    ib = IB()
    ib.connect(
        host=config.ib.host,
        port=config.ib.port,
        clientId=config.ib.client_id
    )
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from ib_async.ib import StartupFetch
from ib_async.ib import StartupFetchALL
from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class LogLevel(str, Enum):
    """Valid log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class IBConfig(BaseSettings):
    """Interactive Brokers connection configuration.
    
    Attributes:
        host: IB Gateway/TWS host address
        port: IB Gateway/TWS port number
        client_id: Unique client identifier
        timeout: Connection timeout in seconds
        readonly: Whether to connect in readonly mode
        account: Specific account to use
        raise_sync_errors: Whether to raise sync errors
        fetch_fields: What to fetch at startup
    """
    model_config = SettingsConfigDict(env_prefix="IB_", validate_default=False)

    # IB Connection Settings
    host: str = "127.0.0.1"
    port: int = Field(default=7497, ge=0, le=65535)
    client_id: int = Field(default=1, gt=0)
    timeout: float = Field(default=4.0, gt=0)
    readonly: bool = False
    account: str = ""
    raise_sync_errors: bool = False
    fetch_fields: StartupFetch = StartupFetchALL

    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host address."""
        if not v:
            raise ValueError("Host cannot be empty")
        return v


class LogConfig(BaseSettings):
    """Logging configuration.
    
    Attributes:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log message format
        file: Log file path (optional)
    """
    model_config = SettingsConfigDict(env_prefix="IB_LOG_", validate_default=False)

    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[Path] = None

    @field_validator('level', mode='before')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level, case insensitive."""
        if isinstance(v, str):
            v = v.upper()
            if v in LogLevel.__members__:
                return v
        return v

    @field_validator('file')
    @classmethod
    def validate_log_file(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate log file path."""
        if v is not None:
            if not v.parent.exists():
                raise ValueError(f"Log directory {v.parent} does not exist")
        return v


class HandlerConfig(BaseSettings):
    """Event handler configuration.
    
    Attributes:
        auto_reconnect: Whether to automatically reconnect on disconnection
        max_retries: Maximum number of reconnection attempts
        retry_delay: Delay between reconnection attempts in seconds
    """
    model_config = SettingsConfigDict(env_prefix="IB_HANDLER_", validate_default=False)

    auto_reconnect: bool = True
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, gt=0)


class Config(BaseSettings):
    """Main configuration class.
    
    Attributes:
        ib: IB connection configuration
        log: Logging configuration
        handler: Handler configuration
    """
    model_config = SettingsConfigDict(env_prefix="", validate_default=False)

    ib: IBConfig = Field(default_factory=IBConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    handler: HandlerConfig = Field(default_factory=HandlerConfig)

    def export_env(self) -> dict[str, str]:
        """Export configuration as environment variables.
        
        Returns:
            Dictionary of environment variable names and values
        """
        env_vars = {}

        # 导出 IB 配置
        ib_dict = self.ib.model_dump()
        for k, v in ib_dict.items():
            if isinstance(v, (str, int, float, bool, Enum)):
                if isinstance(v, Enum):
                    v = v.value
                env_vars[f"IB_{k}".upper()] = str(v)

        # 导出日志配置
        log_dict = self.log.model_dump()
        for k, v in log_dict.items():
            if isinstance(v, (str, int, float, bool, Enum)):
                if isinstance(v, Enum):
                    v = v.value
                env_vars[f"IB_LOG_{k}".upper()] = str(v)

        # 导出处理器配置
        handler_dict = self.handler.model_dump()
        for k, v in handler_dict.items():
            if isinstance(v, (str, int, float, bool, Enum)):
                if isinstance(v, Enum):
                    v = v.value
                env_vars[f"IB_HANDLER_{k}".upper()] = str(v)

        return env_vars
