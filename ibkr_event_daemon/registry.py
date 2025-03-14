"""Event Registry Module.

This module provides functionality for:
1. Registering event handlers through decorators
2. Discovering and loading handlers from environment-specified paths
3. Binding handlers to IB instances
4. Error handling and logging

Example:
    # Set environment variable for handler paths
    os.environ['IB_DAEMON_HANDLERS'] = '/path/to/handlers'

    # Define a handler
    @IBEventRegistry.collect('barUpdate')
    def handle_bar(ib, reqId, bar):
        print(f"Bar data: {bar}")

    # Load handlers and bind to IB instance
    IBEventRegistry.discover_handlers()
    IBEventRegistry.bind_to_ib(ib_instance)
"""

import inspect
import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from eventkit import Event

from .utils import load_hook
from .utils import prepare_task_path


logger = logging.getLogger(__name__)


class IBEventRegistry:
    """Interactive Brokers Event Registry.
    
    A central registry for managing and binding event handlers to IB instances.
    Supports both synchronous and asynchronous handlers with automatic type detection.
    
    Attributes:
        _handlers: A dictionary storing registered handlers.
            Format: {event_name: [{'handler': func, 'is_async': bool, 'file': str, 'name': str}, ...]}
    
    Example:
        # Register a synchronous handler
        @IBEventRegistry.collect('orderStatus')
        def handle_order(ib, order):
            print(f"Order status: {order.status}")
        
        # Register an asynchronous handler
        @IBEventRegistry.collect('barUpdate')
        async def handle_bar(ib, reqId, bar):
            print(f"Bar data: {bar}")
            
        # Bind handlers to IB instance
        IBEventRegistry.bind_to_ib(ib_instance)
    """

    # Store all registered handlers
    _handlers: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def collect(cls, event_name: str) -> Callable:
        """Decorator for registering event handlers.
        
        Automatically detects if a handler is synchronous or asynchronous and registers
        it with the appropriate event.
        
        Args:
            event_name: Name of the IB event to handle.
            
        Returns:
            A decorator function that registers the handler.
            
        Example:
            @IBEventRegistry.collect('orderStatus')
            def handle_order(ib, order):
                print(f"Order status: {order.status}")
                
            @IBEventRegistry.collect('barUpdate')
            async def handle_bar(ib, reqId, bar):
                await process_bar_data(bar)
        """
        def decorator(handler: Callable) -> Callable:
            # Save original handler information
            handler._ib_event = event_name

            # 获取处理器信息
            handler_info = {
                'handler': handler,
                'is_async': inspect.iscoroutinefunction(handler),
                'file': inspect.getfile(handler),
                'name': handler.__name__
            }

            # 注册处理器
            if event_name not in cls._handlers:
                cls._handlers[event_name] = []
            cls._handlers[event_name].append(handler_info)

            return handler
        return decorator

    @classmethod
    def discover_handlers(cls) -> None:
        """Discover and load handlers from environment-specified paths.
        
        Loads handlers from paths specified in the IB_DAEMON_HANDLERS environment variable.
        Multiple paths can be specified using the system path separator.
        
        Example:
            # Windows
            set IB_DAEMON_HANDLERS=C:\\handlers;C:\\another\\handlers
            
            # Linux/Mac
            export IB_DAEMON_HANDLERS=/handlers:/another/handlers
            
            # Load handlers
            IBEventRegistry.discover_handlers()
        """
        # 清空现有处理器
        cls._handlers.clear()

        # 获取处理器路径
        handler_files = prepare_task_path('IB_DAEMON_HANDLERS')
        if not handler_files:
            logger.warning("No handler paths found in IB_DAEMON_HANDLERS")
            return

        # 加载每个处理器文件
        for handler_file in handler_files:
            try:
                # 加载模块
                load_hook(handler_file)
                logger.info(f"Successfully loaded handlers from {handler_file}")
            except Exception as e:
                logger.error(f"Failed to load handlers from {handler_file}: {str(e)}")

    @classmethod
    def bind_to_ib(cls, ib: Any) -> None:
        """Bind registered handlers to an IB instance.
        
        Binds all registered handlers to the given IB instance, automatically handling
        both synchronous and asynchronous handlers.
        
        Args:
            ib: The IB API instance to bind handlers to.
            
        Example:
            # Create IB instance
            ib = IB()
            
            # Register handlers
            @IBEventRegistry.collect('orderStatus')
            def handle_order(ib, order):
                print(f"Order status: {order.status}")
            
            # Bind handlers
            IBEventRegistry.bind_to_ib(ib)
        """
        for event_name, handlers in cls._handlers.items():
            # Get event object
            event: Optional[Event] = getattr(ib, event_name, None)
            if event is None:
                logger.warning(f"Event {event_name} not found in IB instance")
                continue

            # 绑定每个处理器
            for handler_info in handlers:
                try:
                    # 创建带有 ib 实例的处理器
                    handler = handler_info['handler']
                    bound_handler = lambda *args, h=handler: h(ib, *args)

                    # 连接到事件
                    event.connect(bound_handler)
                    logger.info(
                        f"Successfully bound handler {handler_info['name']} "
                        f"from {handler_info['file']} to {event_name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error binding handler {handler_info['name']} to {event_name}: {str(e)}"
                    )
