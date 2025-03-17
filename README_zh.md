[English Documentation](README.md)

# IBKR Event Daemon (中文)

一个灵活的事件驱动守护进程，用于处理盈透证券(Interactive Brokers) TWS/Gateway的实时市场数据和交易事件。

## 特性

- 事件驱动架构，用于处理IBKR市场数据和交易事件
- 简单的处理器模式，便于实现自定义事件处理
- 内置实时K线数据支持
- 支持通过环境变量或命令行选项进行配置
- 全面的日志系统，支持日志轮转和保留策略
- 集成Supervisor进程管理

## 安装

```bash
pip install ibkr-event-daemon
```

## 快速开始

1. 在`.env`文件中配置环境变量：
```
IB_EVENT_DAEMON_HOST=127.0.0.1
IB_EVENT_DAEMON_PORT=7497
IB_EVENT_DAEMON_CLIENTID=1
IB_EVENT_DAEMON_TIMEOUT=4
IB_EVENT_DAEMON_READONLY=False
IB_EVENT_DAEMON_ACCOUNT=
IB_EVENT_DAEMON_RAISESYNCERRORS=False
IB_EVENT_DAEMON_SETUP_PATHS="./example"
```

2. 启动守护进程：
```bash
ibkr-daemon start
```

或者使用自定义日志配置：
```bash
ibkr-daemon start --log-level DEBUG --log-file logs/daemon.log
```

## 创建自定义处理器

处理器是用于处理IBKR事件的Python模块。将您的处理器放在`IB_EVENT_DAEMON_SETUP_PATHS`指定的目录中。

实时K线数据处理器示例（`example/realtimebar_example.py`）：

```python
from ib_async import IB, Forex
from ibkr_event_daemon.core import LoggerType

def setup(ib: IB, logger: LoggerType) -> None:
    usd_jpy = Forex('USDJPY')
    bars = ib.reqRealTimeBars(
        usd_jpy, 
        barSize=5, 
        whatToShow="MIDPOINT", 
        useRTH=True
    )
    bars.updateEvent += onBarUpdate

def onBarUpdate(bars, hasNewBar):
    if hasNewBar:
        print(bars[-1])
```

## 配置管理

配置可以通过以下方式管理：
- 环境变量（`.env`文件）
- 命令行选项
- 配置命令

显示当前配置：
```bash
ibkr-daemon config show
```

初始化默认配置：
```bash
ibkr-daemon config init
```

## 进程管理

项目包含`supervisord.conf`用于进程管理，提供：
- 故障自动重启
- 进程监控
- 日志管理

## 开发

开发模式运行：

1. 克隆仓库
2. 安装依赖：
```bash
pip install -e .
```
3. 创建并配置`.env`文件：
```bash
ibkr-daemon config init
```
4. 启动守护进程：
```bash
python -m ibkr_event_daemon start
```

## 许可证

[MIT License](LICENSE)
