"""Configuration module tests."""
import os
from pathlib import Path
import pytest
from pydantic import ValidationError
from ibkr_event_daemon.config import (
    Config, IBConfig, LogConfig, HandlerConfig,
    LogLevel, StartupFetch, StartupFetchALL
)


@pytest.fixture(autouse=True)
def clean_env():
    """清理环境变量的 fixture.
    
    使用 autouse=True 确保每个测试都会自动运行这个 fixture
    """
    # 保存当前环境变量
    old_env = {}
    for key in list(os.environ.keys()):
        if key.startswith('IB_'):
            old_env[key] = os.environ[key]
            del os.environ[key]
    
    yield
    
    # 恢复环境变量
    for key in list(os.environ.keys()):
        if key.startswith('IB_'):
            del os.environ[key]
    for key, value in old_env.items():
        os.environ[key] = value


@pytest.fixture
def temp_log_dir(tmp_path):
    """创建临时日志目录."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


# IB连接配置测试
def test_ib_config_default_values():
    """测试 IBConfig 的默认值设置."""
    config = IBConfig()
    assert config.host == "127.0.0.1"
    assert config.port == 7497
    assert config.client_id == 1
    assert config.timeout == 4.0
    assert not config.readonly
    assert config.account == ""
    assert not config.raise_sync_errors
    assert config.fetch_fields == StartupFetchALL


def test_ib_config_env_override(clean_env):
    """测试环境变量对 IBConfig 的覆盖."""
    os.environ["IB_HOST"] = "localhost"
    os.environ["IB_PORT"] = "4001"
    os.environ["IB_CLIENT_ID"] = "2"
    
    config = IBConfig()
    assert config.host == "localhost"
    assert config.port == 4001
    assert config.client_id == 2


def test_ib_config_validation():
    """测试 IBConfig 的参数验证."""
    # 测试端口号范围
    with pytest.raises(ValidationError, match="port"):
        IBConfig(port=-1)
    with pytest.raises(ValidationError, match="port"):
        IBConfig(port=65536)
    
    # 测试client_id必须为正数
    with pytest.raises(ValidationError, match="client_id"):
        IBConfig(client_id=0)
    
    # 测试timeout必须为正数
    with pytest.raises(ValidationError, match="timeout"):
        IBConfig(timeout=0)
    
    # 测试host不能为空
    with pytest.raises(ValidationError, match="host"):
        IBConfig(host="")


# 日志配置测试
def test_log_config_default_values():
    """测试 LogConfig 的默认值设置."""
    config = LogConfig()
    assert config.level == LogLevel.INFO
    assert "%(asctime)s" in config.format
    assert config.file is None


def test_log_config_level_validation():
    """测试日志级别验证."""
    # 测试有效的日志级别（大写）
    for level in LogLevel:
        config = LogConfig(level=level.value)
        assert config.level == level

    # 测试有效的日志级别（小写）
    config = LogConfig(level="debug")
    assert config.level == LogLevel.DEBUG
    
    config = LogConfig(level="info")
    assert config.level == LogLevel.INFO
    
    config = LogConfig(level="warning")
    assert config.level == LogLevel.WARNING

    # 测试无效的日志级别
    with pytest.raises(ValidationError, match="Input should be"):
        LogConfig(level="INVALID")


def test_log_file_validation(temp_log_dir):
    """测试日志文件路径验证."""
    # 测试有效的日志文件路径
    log_file = temp_log_dir / "test.log"
    config = LogConfig(file=log_file)
    assert config.file == log_file
    
    # 测试无效的日志目录
    invalid_path = Path("/nonexistent/dir/test.log")
    with pytest.raises(ValidationError, match="directory .* does not exist"):
        LogConfig(file=invalid_path)


# 处理器配置测试
def test_handler_config_default_values():
    """测试 HandlerConfig 的默认值设置."""
    config = HandlerConfig()
    assert config.auto_reconnect is True
    assert config.max_retries == 3
    assert config.retry_delay == 1.0


def test_handler_config_validation():
    """测试处理器配置的参数验证."""
    # 测试重试次数必须为非负数
    with pytest.raises(ValidationError, match="max_retries"):
        HandlerConfig(max_retries=-1)
    
    # 测试重试延迟必须为正数
    with pytest.raises(ValidationError, match="retry_delay"):
        HandlerConfig(retry_delay=0)


# 主配置类测试
def test_config_integration(clean_env):
    """测试配置类的整体集成."""
    # 设置环境变量
    os.environ.update({
        "IB_HOST": "localhost",
        "IB_PORT": "4001",
        "IB_LOG_LEVEL": "DEBUG",
        "IB_HANDLER_MAX_RETRIES": "5"
    })

    config = Config()

    # 验证IB配置
    assert config.ib.host == "localhost"
    assert config.ib.port == 4001

    # 验证日志配置
    assert config.log.level == LogLevel.DEBUG

    # 验证处理器配置
    assert config.handler.max_retries == 5

    # 验证其他值保持默认
    assert config.ib.timeout == 4.0
    assert config.log.file is None
    assert config.handler.retry_delay == 1.0


def test_config_export():
    """测试配置导出功能."""
    config = Config(
        ib=IBConfig(
            host="localhost",
            port=4001,
            client_id=2,
            readonly=True
        ),
        log=LogConfig(
            level=LogLevel.DEBUG,
            format="%(message)s"
        ),
        handler=HandlerConfig(
            auto_reconnect=False,
            max_retries=5,
            retry_delay=2.0
        )
    )
    
    env_vars = config.export_env()
    
    # 验证 IB 配置
    assert env_vars["IB_HOST"] == "localhost"
    assert env_vars["IB_PORT"] == "4001"
    assert env_vars["IB_CLIENT_ID"] == "2"
    assert env_vars["IB_READONLY"] == "True"
    
    # 验证日志配置
    assert env_vars["IB_LOG_LEVEL"] == "DEBUG"
    assert env_vars["IB_LOG_FORMAT"] == "%(message)s"
    
    # 验证处理器配置
    assert env_vars["IB_HANDLER_AUTO_RECONNECT"] == "False"
    assert env_vars["IB_HANDLER_MAX_RETRIES"] == "5"
    assert env_vars["IB_HANDLER_RETRY_DELAY"] == "2.0"


def test_empty_config_validation():
    """测试空配置的处理."""
    # 测试完全默认配置
    config = Config()
    assert config.ib.host == "127.0.0.1"
    assert config.log.level == LogLevel.INFO
    assert config.handler.auto_reconnect is True


@pytest.mark.parametrize("readonly,account,expected_error", [
    (True, "", None),  # 只读模式，无账户，有效
    (False, "", None),  # 非只读模式，无账户，有效
    (True, "123", None),  # 只读模式，有账户，有效
])
def test_invalid_config_combinations(readonly, account, expected_error):
    """测试配置组合."""
    if expected_error:
        with pytest.raises(ValidationError, match=expected_error):
            IBConfig(readonly=readonly, account=account)
    else:
        config = IBConfig(readonly=readonly, account=account)
        assert config.readonly == readonly
        assert config.account == account
