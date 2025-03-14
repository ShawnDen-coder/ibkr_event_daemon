"""Tests for the core module.

This module contains unit tests for the IBEventDaemon class.
"""
from typing import Generator
import asyncio
import pytest
from pytest_mock import MockerFixture
from ib_async import IB
from ibkr_event_daemon.core import IBEventDaemon
from ibkr_event_daemon.config import Config
from ibkr_event_daemon.registry import IBEventRegistry


@pytest.fixture
def mock_ib(mocker: MockerFixture) -> Generator[IB, None, None]:
    """Create a mock IB API client.
    
    Args:
        mocker: pytest-mock fixture
    
    Yields:
        Mock IB client instance
    """
    mock = mocker.MagicMock(spec=IB)
    mock.isConnected.return_value = False
    mock.run = mocker.MagicMock()
    
    # 创建异步 mock 方法
    async def mock_connect(*args, **kwargs):
        return None
    mock.connect = mocker.MagicMock(side_effect=mock_connect)
    
    async def mock_disconnect(*args, **kwargs):
        return None
    mock.disconnect = mocker.MagicMock(side_effect=mock_disconnect)
    
    yield mock


@pytest.fixture
def config() -> Config:
    """Create a test configuration.
    
    Returns:
        Test configuration instance
    """
    return Config(
        ib={"host": "127.0.0.1", "port": 7497},
        handler={"max_retries": 2, "retry_delay": 0.1}
    )


@pytest.fixture
def registry(mocker: MockerFixture) -> IBEventRegistry:
    """Create a test event registry.
    
    Returns:
        Test registry instance
    """
    registry = IBEventRegistry()
    registry.bind_to_ib = mocker.MagicMock()
    return registry


@pytest.fixture
def daemon(
    mock_ib: IB,
    config: Config,
    registry: IBEventRegistry,
    mocker: MockerFixture
) -> IBEventDaemon:
    """Create a test daemon instance.
    
    Args:
        mock_ib: Mock IB client
        config: Test configuration
        registry: Test registry
    
    Returns:
        Test daemon instance
    """
    # 创建一个假的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 模拟 asyncio.sleep
    async def mock_sleep(*args, **kwargs):
        return None
    mocker.patch('asyncio.sleep', side_effect=mock_sleep)
    
    return IBEventDaemon(config=config, registry=registry, ib=mock_ib)


def test_daemon_initialization(
    daemon: IBEventDaemon,
    mock_ib: IB,
    config: Config,
    registry: IBEventRegistry,
    mocker: MockerFixture
) -> None:
    """Test daemon initialization.
    
    Should:
    1. Create IB instance
    2. Initialize logger
    3. Bind registry to IB instance
    """
    # 验证实例属性
    assert daemon.config == config
    assert daemon.registry == registry
    assert daemon.ib == mock_ib
    
    # 验证注册中心绑定
    assert registry.bind_to_ib.call_count == 1
    assert registry.bind_to_ib.call_args[0][0] == mock_ib


def test_daemon_start(
    daemon: IBEventDaemon,
    mock_ib: IB,
    mocker: MockerFixture
) -> None:
    """Test daemon start method.
    
    Should:
    1. Connect to IB
    2. Start event loop
    """
    # 模拟连接成功
    mock_ib.isConnected.return_value = True
    
    # 让事件循环运行一次后抛出异常来停止
    mock_ib.run.side_effect = Exception("Stop")
    
    # 运行守护进程
    with pytest.raises(Exception, match="Stop"):
        daemon.start()
    
    # 验证调用
    assert mock_ib.connect.call_count == 1
    assert mock_ib.run.call_count == 1


@pytest.mark.asyncio
async def test_daemon_connect_success(
    daemon: IBEventDaemon,
    mock_ib: IB
) -> None:
    """Test successful connection.
    
    Should connect on first attempt if successful.
    """
    # 模拟连接成功
    mock_ib.isConnected.return_value = True
    
    # 尝试连接
    await daemon.connect()
    
    # 验证调用
    assert mock_ib.connect.call_count == 1


@pytest.mark.asyncio
async def test_daemon_connect_retry(
    daemon: IBEventDaemon,
    mock_ib: IB,
    mocker: MockerFixture
) -> None:
    """Test connection retry logic.
    
    Should retry connection up to max_retries times.
    """
    # 模拟连接失败然后成功
    mock_ib.isConnected.side_effect = [False, False, True]
    
    # 创建异步 mock 方法
    async def mock_connect_fail(*args, **kwargs):
        raise Exception("Connection failed")
    
    async def mock_connect_success(*args, **kwargs):
        return None
    
    mock_ib.connect.side_effect = [
        mock_connect_fail(),
        mock_connect_fail(),
        mock_connect_success()
    ]
    
    # 尝试连接
    await daemon.connect()
    
    # 验证重试次数
    assert mock_ib.connect.call_count == 3


@pytest.mark.asyncio
async def test_daemon_connect_failure(
    daemon: IBEventDaemon,
    mock_ib: IB,
    mocker: MockerFixture
) -> None:
    """Test connection failure.
    
    Should raise ConnectionError after max retries.
    """
    # 模拟连接始终失败
    mock_ib.isConnected.return_value = False
    
    # 创建异步 mock 方法
    async def mock_connect_fail(*args, **kwargs):
        raise Exception("Connection failed")
    
    mock_ib.connect.side_effect = mock_connect_fail
    
    # 验证异常
    with pytest.raises(ConnectionError):
        await daemon.connect()
    
    # 验证尝试次数
    assert mock_ib.connect.call_count == daemon.config.handler.max_retries + 1


def test_daemon_stop(
    daemon: IBEventDaemon,
    mock_ib: IB
) -> None:
    """Test daemon stop method.
    
    Should disconnect from IB.
    """
    # 模拟已连接状态
    mock_ib.isConnected.return_value = True
    
    # 停止守护进程
    daemon.stop()
    
    # 验证断开连接
    assert mock_ib.disconnect.call_count == 1


def test_daemon_disconnect_error(
    daemon: IBEventDaemon,
    mock_ib: IB
) -> None:
    """Test disconnect error handling.
    
    Should log error but not raise exception.
    """
    # 模拟断开连接错误
    mock_ib.isConnected.return_value = True
    
    async def mock_disconnect_fail(*args, **kwargs):
        raise Exception("Disconnect error")
    
    mock_ib.disconnect.side_effect = mock_disconnect_fail
    
    # 断开连接不应抛出异常
    daemon.disconnect()
