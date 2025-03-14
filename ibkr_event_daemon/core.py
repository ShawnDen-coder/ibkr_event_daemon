"""Core module for IB event daemon.

This module provides the main daemon interface for interacting with Interactive Brokers API.

Example:
    Basic usage of IBEventDaemon:
    
    >>> from ibkr_event_daemon.config import Config
    >>> from ibkr_event_daemon.registry import IBEventRegistry
    >>> 
    >>> # 创建配置和注册中心
    >>> config = Config(
    ...     ib={"host": "127.0.0.1", "port": 7497},
    ...     handler={"max_retries": 3, "retry_delay": 5.0}
    ... )
    >>> registry = IBEventRegistry()
    >>> 
    >>> # 初始化并启动守护进程
    >>> daemon = IBEventDaemon(config, registry)
    >>> daemon.start()  # 这会阻塞直到连接断开
"""
import logging
import asyncio
from typing import NoReturn, Optional
from ib_async import IB
from ibkr_event_daemon.config import Config
from ibkr_event_daemon.registry import IBEventRegistry


class IBEventDaemon:
    """Interactive Brokers event daemon.
    
    This class implements a daemon process that manages IB API connection
    and provides direct IB instance access to handlers.
    
    Attributes:
        config: Configuration instance containing IB connection and handler settings.
        registry: Event registry instance for managing event handlers.
        ib: IB API client instance, accessible by handlers.
    
    Example:
        >>> daemon = IBEventDaemon(config, registry)
        >>> try:
        ...     daemon.start()  # 阻塞直到连接断开
        ... except ConnectionError as e:
        ...     print(f"Failed to connect: {e}")
        ... finally:
        ...     daemon.stop()
    """
    
    def __init__(self, config: Config, registry: IBEventRegistry, ib: Optional[IB] = None) -> None:
        """Initialize the IB event daemon.
        
        Args:
            config: Configuration instance containing connection settings.
            registry: Event registry instance for managing handlers.
            ib: Optional IB client instance for testing.
        
        Example:
            >>> config = Config(
            ...     ib={"host": "127.0.0.1", "port": 7497},
            ...     handler={"max_retries": 3, "retry_delay": 5.0}
            ... )
            >>> registry = IBEventRegistry()
            >>> daemon = IBEventDaemon(config, registry)
        """
        self.config = config
        self.registry = registry
        self.ib = ib or IB()
        self._logger = logging.getLogger(__name__)
        
        # 绑定注册中心到 IB 实例，使处理器可以访问
        self.registry.bind_to_ib(self.ib)
    
    def start(self) -> NoReturn:
        """Start the event daemon.
        
        This method connects to IB if not already connected and starts
        the event loop. It blocks until the connection is lost or an error occurs.
        
        Raises:
            ConnectionError: If initial connection fails.
        
        Example:
            >>> try:
            ...     daemon.start()
            ... except ConnectionError as e:
            ...     print(f"Connection failed: {e}")
        """
        # 确保在事件循环中运行连接
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.connect())
        
        self._logger.info("Starting IB event loop")
        self.ib.run()
    
    async def connect(self) -> None:
        """Connect to IB API.
        
        Attempts to connect to IB Gateway/TWS with configured retry policy.
        
        Raises:
            ConnectionError: If connection fails after max retries.
        
        Example:
            >>> try:
            ...     await daemon.connect()
            ... except ConnectionError as e:
            ...     print(f"Failed to connect after retries: {e}")
        """
        for attempt in range(self.config.handler.max_retries + 1):
            try:
                await self._try_connect()
                return
            except Exception as e:
                self._handle_connect_error(e, attempt)
                if attempt < self.config.handler.max_retries:
                    await asyncio.sleep(self.config.handler.retry_delay)
        
        raise ConnectionError(
            f"Failed to connect after {self.config.handler.max_retries + 1} attempts"
        )
    
    async def _try_connect(self) -> None:
        """Attempt to establish connection to IB.
        
        Raises:
            ConnectionError: If connection cannot be established.
        """
        self._logger.info(
            "Connecting to IB %s:%d",
            self.config.ib.host,
            self.config.ib.port
        )
        
        await self.ib.connect(
            host=self.config.ib.host,
            port=self.config.ib.port,
            clientId=self.config.ib.client_id,
            timeout=self.config.ib.timeout,
            readonly=self.config.ib.readonly,
            account=self.config.ib.account
        )
        
        if self.ib.isConnected():
            self._logger.info("Successfully connected to IB")
        else:
            raise ConnectionError("Failed to establish connection")
    
    def _handle_connect_error(self, error: Exception, attempt: int) -> None:
        """Handle connection error and retry logic.
        
        Args:
            error: The connection error that occurred.
            attempt: Current attempt number, starting from 0.
        """
        self._logger.error("Failed to connect to IB: %s", str(error))
    
    def stop(self) -> None:
        """Stop the daemon.
        
        Example:
            >>> daemon.stop()  # 优雅地停止守护进程
        """
        self._logger.info("Stopping IB daemon")
        self.disconnect()
    
    def disconnect(self) -> None:
        """Disconnect from IB API.
        
        Any errors during disconnection are logged but not raised.
        
        Example:
            >>> daemon.disconnect()  # 断开与 IB 的连接
        """
        try:
            if self.ib.isConnected():
                self._logger.info("Disconnecting from IB")
                self.ib.disconnect()
        except Exception as e:
            self._logger.error("Error during disconnect: %s", str(e))
