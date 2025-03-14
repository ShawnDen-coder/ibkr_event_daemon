"""Pytest configuration file."""
import pytest


@pytest.fixture(autouse=True)
def setup_test():
    """Setup any state specific to the execution of the given test case."""
    # 设置
    yield
    # 清理
    # 重置 IBEventRegistry 的状态
    from ibkr_event_daemon.registry import IBEventRegistry
    IBEventRegistry._handlers.clear()
