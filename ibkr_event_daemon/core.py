"""Core module for the IBKR event daemon.

This module provides the main components for interacting with Interactive Brokers TWS/Gateway.
It includes the core client wrapper and hook system for handling market data and events.

The module consists of two main components:
    - IBKRClient: A high-level wrapper for managing IB connections and event handlers
    - HookModule: A protocol defining the interface for event hook modules

Example:
    >>> from ibkr_event_daemon.core import IBKRClient
    >>> from ibkr_event_daemon.config import IbkrSettings
    >>> 
    >>> # Create client with custom settings
    >>> config = IbkrSettings(port=4002)  # Use paper trading port
    >>> client = IBKRClient(config=config)
    >>> 
    >>> # Start the client (this will block until interrupted)
    >>> client.excute()
"""

from typing import Protocol

from ib_async import IB
from loguru import logger
from typing_extensions import Optional

from ibkr_event_daemon import utils
from ibkr_event_daemon.config import IbkrSettings
from ibkr_event_daemon.constants import ENV_PREFIX


LoggerType = logger.__class__


class HookModule(Protocol):
    """Protocol defining the interface for IBKR event hook modules.

    This protocol defines the required interface that hook modules must implement
    to be used with the IBKR event daemon.

    Example:
        >>> class MyHook:
        ...     def setup(self, ib: IB, logger: LoggerType) -> None:
        ...         contract = Forex('EURUSD')
        ...         ib.reqMktData(contract)
    """

    def setup(self, ib: IB, logger: LoggerType) -> None:
        """Set up the hook module with IB client and logger instances.

        Args:
            ib: Interactive Brokers client instance.
            logger: Logger instance for recording events and errors.

        Example:
            >>> def setup(self, ib, logger):
            ...     # Subscribe to EURUSD market data
            ...     contract = Forex('EURUSD')
            ...     ib.reqMktData(contract)
            ...     logger.info("Subscribed to EURUSD market data")
        """
        ...


class IBKRClient:
    """Interactive Brokers client wrapper for event handling.

    This class provides a high-level interface for connecting to Interactive Brokers,
    setting up event handlers, and managing the connection lifecycle.

    Attributes:
        ib: Interactive Brokers client instance.
        config: Configuration settings for the IBKR connection.

    Example:
        >>> # Create client with default settings
        >>> client = IBKRClient()
        >>> # Create client with custom settings
        >>> config = IbkrSettings(host='127.0.0.1', port=7497)
        >>> client = IBKRClient(config=config)
        >>> # Start the client
        >>> client.excute()
    """

    def __init__(self, ib: Optional[IB] = None, config: Optional[IbkrSettings] = None):
        """Initialize the IBKR client wrapper.

        Args:
            ib: Optional Interactive Brokers client instance. If not provided, a new one will be created.
            config: Optional IbkrSettings instance. If not provided, a new instance with default values will be created.

        Example:
            >>> # Create with custom IB instance
            >>> ib = IB()
            >>> client = IBKRClient(ib=ib)
            >>> # Create with custom config
            >>> config = IbkrSettings(port=4002)  # Use paper trading port
            >>> client = IBKRClient(config=config)
        """
        self.ib: IB = ib or IB()
        self.config:IbkrSettings = config or IbkrSettings()

    def _setup_ib_session(self):
        """Set up and establish connection to TWS/Gateway.

        Connects to Interactive Brokers using the configured settings and logs the connection attempt.

        Example:
            >>> client = IBKRClient()
            >>> client._setup_ib_session()
            >>> assert client.ib.isConnected()
        """
        logger.info("start connect TWS ...")
        _config = self.config.model_dump(by_alias=True, exclude="setup_paths")
        logger.debug(f"loading ibkr config: {_config}")
        self.ib.connect(**_config)

    def _setup_callback(self):
        """Set up event callbacks from configured hook modules.

        Loads and initializes hook modules specified in the environment variable
        defined by constants.ENV_PREFIX + 'SETUP_PATHS'. Each hook module is
        initialized with the IB client and logger instances.

        Example:
            >>> # Assuming IB_EVENT_DAEMON_SETUP_PATHS points to valid hook modules
            >>> client = IBKRClient()
            >>> client._setup_callback()  # Loads and initializes all hooks
        """
        env_var = f"{ENV_PREFIX}SETUP_PATHS"
        files = utils.prepare_task_path(env_var)
        logger.info(f"get setup file hooks: {files}")
        for item in files:
            moudle: Optional[HookModule] = utils.load_hook(item)
            if not moudle:
                continue
            try:
                moudle.setup(self.ib, logger)
                logger.info(f"setup callback func {moudle.__name__}")
            except AttributeError as e:
                logger.exception(f"load moudle {moudle.__name__} error: \n {e}")

    def setup(self):
        """Initialize the IBKR client and set up event handlers.

        Establishes connection to TWS/Gateway if not already connected and sets up event callbacks.

        Example:
            >>> client = IBKRClient()
            >>> client.setup()  # Connects and sets up handlers
            >>> assert client.ib.isConnected()
        """
        if not self.ib.isConnected():
            self._setup_ib_session()
        self._setup_callback()

    def pre_action(self):
        """Perform pre-run setup actions.

        Ensures the client is properly configured before starting the event loop.

        Example:
            >>> client = IBKRClient()
            >>> client.pre_action()  # Performs all necessary setup
        """
        self.setup()

    def stop(self):
        """Stop the IBKR client and clean up resources.

        Disconnects from TWS/Gateway and logs the shutdown.

        Example:
            >>> client = IBKRClient()
            >>> client.setup()
            >>> client.stop()  # Disconnects from TWS
            >>> assert not client.ib.isConnected()
        """
        logger.info("Stopping the IBKR daemon ...")
        self.ib.disconnect()

    def excute(self) -> None:
        """Execute the main event loop.

        Starts the event loop and handles keyboard interrupts for graceful shutdown.

        Example:
            >>> client = IBKRClient()
            >>> # This will block until interrupted
            >>> client.excute()  # Starts the event loop
        """
        try:
            self.pre_action()
            self.ib.run()
        except KeyboardInterrupt:
            self.stop()
            logger.info("Program interrupted and stopped.")


if __name__ == "__main__":
    from ibkr_event_daemon.utils import setup_logger
    
    # Setup logger with default settings
    setup_logger(log_level="DEBUG")
    
    ib = IBKRClient()
    ib.excute()
