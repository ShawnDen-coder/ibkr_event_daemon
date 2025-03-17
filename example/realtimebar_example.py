"""Example module demonstrating real-time bar data subscription from IBKR.

This module shows how to set up a real-time bar data subscription for USD/JPY forex pair
using the IBKR API. It demonstrates the event-driven approach to handling bar updates.

Example:
    To use this example, ensure it's in your IBKR_SETUP_PATHS and run the daemon:

    >>> from ibkr_event_daemon.core import IBKRClient
    >>> client = IBKRClient()
    >>> client.excute()  # This will start receiving USD/JPY bars
"""

from ib_async import IB
from ib_async import Forex

from ibkr_event_daemon.core import LoggerType


def setup(ib: IB, logger: LoggerType) -> None:
    """Set up real-time bar subscription for USD/JPY forex pair.

    This function is called by the IBKR event daemon to initialize the bar data
    subscription. It subscribes to 5-second bars for USD/JPY using midpoint prices.

    Args:
        ib: Interactive Brokers client instance.
        logger: Logger instance for recording events and errors.

    Example:
        >>> def setup(ib, logger):
        ...     usd_jpy = Forex('USDJPY')
        ...     bars = ib.reqRealTimeBars(
        ...         usd_jpy, 
        ...         barSize=5,
        ...         whatToShow="MIDPOINT",
        ...         useRTH=True
        ...     )
        ...     bars.updateEvent += onBarUpdate
    """
    usd_jpy = Forex('USDJPY')
    bars = ib.reqRealTimeBars(usd_jpy, barSize=5, whatToShow="MIDPOINT", useRTH=True)
    bars.updateEvent += onBarUpdate


def onBarUpdate(bars, hasNewBar):
    """Handle real-time bar updates.

    Callback function that is triggered when new bar data is received.
    Prints the latest bar when a new bar is completed.

    Args:
        bars: Collection of bar data, with the latest bar at index -1.
        hasNewBar: Boolean indicating if a new bar has been completed.

    Example:
        >>> def onBarUpdate(bars, hasNewBar):
        ...     if hasNewBar:
        ...         latest_bar = bars[-1]
        ...         print(f"Time: {latest_bar.time}, Close: {latest_bar.close}")
    """
    if hasNewBar:
        print(bars[-1])
