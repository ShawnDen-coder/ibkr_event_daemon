"""Test cases for the registry module."""
import os
import pytest
import inspect
from pytest_mock import MockerFixture
from typing import Dict, List, Any, Callable, Union
from eventkit import Event

from ibkr_event_daemon.registry import IBEventRegistry


def create_sync_handler(ib, *args, **kwargs) -> None:
    """同步处理器函数"""
    assert hasattr(ib, 'connect')


async def create_async_handler(ib, *args, **kwargs) -> None:
    """异步处理器函数"""
    assert hasattr(ib, 'connect')


@pytest.mark.parametrize("event_name", [
    'orderStatus',
    'error',
    'tickPrice',
    'accountSummary'
])
def test_collect_sync_handler(event_name: str):
    """测试同步处理器的装饰器.
    
    Args:
        event_name: 事件名称
    """
    decorated_handler = IBEventRegistry.collect(event_name)(create_sync_handler)
    
    assert hasattr(decorated_handler, '_ib_event')
    assert decorated_handler._ib_event == event_name
    assert not inspect.iscoroutinefunction(decorated_handler)


@pytest.mark.parametrize("event_name", [
    'barUpdate',
    'newTrade',
    'scannerData',
    'historicalData'
])
def test_collect_async_handler(event_name: str):
    """测试异步处理器的装饰器.
    
    Args:
        event_name: 事件名称
    """
    decorated_handler = IBEventRegistry.collect(event_name)(create_async_handler)
    
    assert hasattr(decorated_handler, '_ib_event')
    assert decorated_handler._ib_event == event_name
    assert inspect.iscoroutinefunction(decorated_handler)


@pytest.mark.parametrize("event_name,handler_args", [
    ('orderStatus', ['order']),
    ('error', ['reqId', 'errorCode', 'errorString']),
    ('barUpdate', ['reqId', 'bar']),
    ('tickPrice', ['reqId', 'field', 'price', 'attribs'])
])
def test_handler_signature(event_name: str, handler_args: List[str]):
    """测试处理器的参数签名.
    
    Args:
        event_name: 事件名称
        handler_args: 处理器函数的参数列表
    """
    def handler(ib, *args):
        assert len(args) == len(handler_args)
    
    decorated_handler = IBEventRegistry.collect(event_name)(handler)
    assert hasattr(decorated_handler, '_ib_event')
    
    # 创建一个带有正确参数数量的调用
    mock_ib = type('MockIB', (), {'connect': lambda: None})()
    args = [None] * len(handler_args)  # 创建对应数量的参数
    decorated_handler(mock_ib, *args)  # 验证调用不会抛出异常


def test_handler_ib_instance_access():
    """测试处理器是否能正确访问 IB 实例."""
    ib_accessed = False
    
    def handler(ib, *args):
        nonlocal ib_accessed
        ib_accessed = hasattr(ib, 'connect')
    
    decorated_handler = IBEventRegistry.collect('test')(handler)
    mock_ib = type('MockIB', (), {'connect': lambda: None})()
    decorated_handler(mock_ib)
    
    assert ib_accessed


@pytest.mark.parametrize("env_paths,expected_files", [
    ("/path/to/handlers", ["/path/to/handlers/order.py"]),
    ("/path/to/handlers:/another/path", ["/path/to/handlers/order.py", "/another/path/market.py"]),
    ("", [])
])
def test_discover_handlers(mocker: MockerFixture, env_paths: str, expected_files: List[str]):
    """Test handler discovery from environment variable paths."""
    # Mock 环境变量
    mock_env = {'IB_DAEMON_HANDLERS': env_paths}
    mocker.patch.dict(os.environ, mock_env)
    
    # Mock utils.prepare_task_path
    mock_prepare_path = mocker.patch(
        'ibkr_event_daemon.registry.prepare_task_path',
        return_value=expected_files
    )
    
    # Mock utils.load_hook
    def create_mock_handler(event_name: str, is_async: bool = False) -> Callable:
        if is_async:
            async def handler(ib, *args): pass
        else:
            def handler(ib, *args): pass
        return IBEventRegistry.collect(event_name)(handler)
    
    def mock_module():
        return type('Module', (), {
            'handle_order': create_mock_handler('orderStatus'),
            'handle_market': create_mock_handler('barUpdate', True)
        })
    
    mock_load_hook = mocker.patch(
        'ibkr_event_daemon.registry.load_hook',
        return_value=mock_module()
    )
    
    # 执行处理器发现
    IBEventRegistry.discover_handlers()
    
    # 验证
    mock_prepare_path.assert_called_once_with('IB_DAEMON_HANDLERS')
    assert mock_load_hook.call_count == len(expected_files)


@pytest.mark.parametrize("event_config", [
    {
        'name': 'orderStatus',
        'handlers': [
            {'sync': True, 'args': ('order',)},
            {'sync': False, 'args': ('order',)}
        ]
    },
    {
        'name': 'barUpdate',
        'handlers': [
            {'sync': False, 'args': ('reqId', 'bar')},
            {'sync': True, 'args': ('reqId', 'bar')}
        ]
    },
    {
        'name': 'error',
        'handlers': [
            {'sync': True, 'args': ('reqId', 'errorCode', 'errorString')}
        ]
    }
])
def test_bind_to_ib(mocker: MockerFixture, event_config: Dict):
    """Test binding handlers to IB instance."""
    # 创建模拟的IB实例和事件
    mock_event = mocker.Mock(spec=Event)
    mock_ib = mocker.Mock()
    setattr(mock_ib, event_config['name'], mock_event)
    
    handlers_info = []
    for handler_config in event_config['handlers']:
        # 动态创建处理器函数
        args_str = ', '.join(['ib'] + list(handler_config['args']))
        handler_code = f"{'async ' if not handler_config['sync'] else ''}def handler({args_str}): pass"
        
        namespace = {}
        exec(handler_code, globals(), namespace)
        handler = namespace['handler']
        decorated_handler = IBEventRegistry.collect(event_config['name'])(handler)
        
        handlers_info.append({
            'handler': decorated_handler,
            'is_async': inspect.iscoroutinefunction(decorated_handler),
            'file': 'test.py',
            'name': f"{'async_' if not handler_config['sync'] else ''}handler"
        })
    
    # 添加处理器到注册中心
    IBEventRegistry._handlers = {event_config['name']: handlers_info}
    
    # 执行绑定
    IBEventRegistry.bind_to_ib(mock_ib)
    
    # 验证
    assert mock_event.connect.call_count == len(event_config['handlers'])


@pytest.mark.parametrize("error_type,expected_log", [
    (ConnectionError("Failed to connect"), "Error binding handler"),
    (ValueError("Invalid parameter"), "Error binding handler"),
    (Exception("Unknown error"), "Error binding handler")
])
def test_bind_to_ib_error_handling(mocker: MockerFixture, caplog, 
                                 error_type: Exception, expected_log: str):
    """Test error handling during binding process."""
    # 创建模拟的IB实例和事件
    mock_event = mocker.Mock(spec=Event)
    mock_event.connect.side_effect = error_type
    mock_ib = mocker.Mock()
    mock_ib.orderStatus = mock_event
    
    # 设置测试处理器
    @IBEventRegistry.collect('orderStatus')
    def handler(ib, order): pass
    
    # 添加处理器到注册中心
    IBEventRegistry._handlers = {
        'orderStatus': [
            {'handler': handler, 
             'is_async': inspect.iscoroutinefunction(handler),
             'file': 'test.py', 
             'name': 'handler'}
        ]
    }
    
    # 执行绑定
    IBEventRegistry.bind_to_ib(mock_ib)
    
    # 验证错误日志
    assert expected_log in caplog.text


@pytest.mark.parametrize("bar_data", [
    {
        'date': '2025-03-14 12:57:00',
        'open': 100.0,
        'high': 101.0,
        'low': 99.0,
        'close': 100.5,
        'volume': 1000,
        'wap': 100.2,
        'count': 10
    },
    {
        'date': '2025-03-14 12:57:05',
        'open': 100.5,
        'high': 102.0,
        'low': 100.0,
        'close': 101.5,
        'volume': 500,
        'wap': 101.0,
        'count': 5
    }
])
def test_realtime_bar_handler(mocker: MockerFixture, bar_data: Dict[str, Union[str, float, int]]):
    """Test realtime bar data handling."""
    # 创建模拟的IB实例和事件
    mock_event = mocker.Mock(spec=Event)
    mock_ib = mocker.Mock()
    mock_ib.barUpdate = mock_event
    mock_ib.reqRealTimeBars = mocker.Mock()  # 添加这个 mock
    
    # 设置测试处理器
    received_data = {}
    
    @IBEventRegistry.collect('barUpdate')
    def handle_bar_update(ib, reqId: int, bar: Dict[str, Any]) -> None:
        # 验证能访问IB实例
        assert hasattr(ib, 'reqRealTimeBars')
        # 保存接收到的数据
        received_data.update(bar)
        # 测试能通过IB实例发送新请求
        ib.reqRealTimeBars(reqId, "AAPL", "SMART", "TRADES", 5)
    
    # 添加处理器到注册中心
    IBEventRegistry._handlers = {
        'barUpdate': [
            {'handler': handle_bar_update, 
             'is_async': inspect.iscoroutinefunction(handle_bar_update),
             'file': 'test.py', 
             'name': 'handle_bar_update'}
        ]
    }
    
    # 执行绑定
    IBEventRegistry.bind_to_ib(mock_ib)
    
    # 获取绑定的处理器
    bound_handler = mock_event.connect.call_args[0][0]
    
    # 直接调用绑定的处理器
    bound_handler(1, bar_data)
    
    # 验证
    assert mock_event.connect.called
    assert mock_ib.reqRealTimeBars.called
    assert received_data == bar_data
    mock_ib.reqRealTimeBars.assert_called_once_with(1, "AAPL", "SMART", "TRADES", 5)
