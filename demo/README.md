# IB Async 事件桥接模块

这是一个用于连接 Interactive Brokers (IB) API 的 eventkit 事件系统和 blinker 信号系统的桥接模块，提供增强的事件处理能力。

## 主要特性

- 无缝集成 eventkit 和 blinker 事件系统
- 非侵入式的 eventkit 事件补丁
- 支持事件处理器的弱引用
- 支持命名空间隔离
- 支持临时事件订阅
- 事件系统间的错误隔离

## 安装

事件桥接模块是 `ib_async` 包的一部分，如果你已经安装了该包，无需额外安装。

依赖项：
- eventkit
- blinker

## 快速开始

### 全局事件桥接

```python
from ib_async.event_bridge import EventBridge
from blinker import signal
from ib_async import IB

# 在创建任何 IB 实例之前启用事件桥接
EventBridge.patch()

# 创建 IB 实例
ib = IB()

# 使用 blinker 订阅事件
@signal('connectedEvent').connect
def on_connected(sender):
    print("已连接到 IB!")

@signal('orderStatusEvent').connect
def on_order_status(sender, trade):
    print(f"订单状态变更: {trade.order.orderId} - {trade.orderStatus.status}")

# 正常使用 IB API
await ib.connectAsync('127.0.0.1', 7497, clientId=1)
```

### 高级用法

#### 弱引用订阅

```python
# 使用弱引用避免内存泄漏
signal('orderStatusEvent').connect(handler, weak=True)
```

#### 命名空间隔离

```python
from blinker import Namespace

# 创建独立的信号命名空间
my_signals = Namespace()
order_signal = my_signals.signal('orderStatusEvent')

@order_signal.connect
def my_handler(sender, trade):
    print(f"处理订单: {trade.order.orderId}")
```

#### 临时订阅

```python
# 仅在特定上下文中订阅事件
with signal('orderStatusEvent').connected_to(handler):
    await ib.placeOrder(contract, order)
```

#### 过滤订阅

```python
@signal('orderStatusEvent').connect_via(lambda sender: sender.name == 'specific_event')
def handle_specific_order(sender, trade):
    print(f"处理特定订单: {trade.order.orderId}")
```

## API 参考

### EventBridge 类

#### 方法

- `patch()`: 为所有 eventkit 事件启用桥接
- `unpatch()`: 禁用事件桥接并恢复原始行为
- `get_signal(event_name: str)`: 获取指定事件名称的 blinker 信号

## 可用事件

所有来自 IB API 的事件都可以作为 blinker 信号使用，事件名称保持不变：

- `connectedEvent`: 连接事件
- `disconnectedEvent`: 断开连接事件
- `updateEvent`: 更新事件
- `pendingTickersEvent`: 待处理行情事件
- `barUpdateEvent`: K线更新事件
- `newOrderEvent`: 新订单事件
- `orderModifyEvent`: 订单修改事件
- `cancelOrderEvent`: 订单取消事件
- `openOrderEvent`: 未完成订单事件
- `orderStatusEvent`: 订单状态事件
- `execDetailsEvent`: 执行详情事件
- `commissionReportEvent`: 佣金报告事件
- `updatePortfolioEvent`: 投资组合更新事件
- `positionEvent`: 持仓事件
- `accountValueEvent`: 账户价值事件
- `accountSummaryEvent`: 账户摘要事件

## 最佳实践

1. 始终在创建 IB 实例之前启用事件桥接
2. 对于长期运行的应用程序，使用弱引用
3. 复杂应用程序建议使用命名空间
4. 确保在事件处理器中妥善处理异常
5. 适时使用临时订阅功能

## 错误处理

事件桥接模块设计了错误隔离机制：
- blinker 处理器中的异常不会影响 eventkit 处理器
- 所有桥接错误都会被记录，但不会导致应用程序崩溃

## 问题反馈

如果你发现任何问题或有功能改进建议，欢迎提交 issue！
