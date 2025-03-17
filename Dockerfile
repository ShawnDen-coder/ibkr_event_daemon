# 使用官方 Python 3.12 精简版镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# PYTHONUNBUFFERED=1: 强制 Python 不缓冲标准输出，立即将输出写入日志文件，对容器日志记录很重要
# PYTHONDONTWRITEBYTECODE=1: 不生成 .pyc 文件（Python 字节码），减少容器大小
# PIP_NO_CACHE_DIR=1: 禁用 pip 的缓存，减少容器大小
# PIP_DISABLE_PIP_VERSION_CHECK=1: 禁用 pip 版本检查，加快构建速度
# IB_EVENT_DAEMON_SETUP_PATHS: 设置事件处理器的路径，指向容器中的 example 目录
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    IB_EVENT_DAEMON_SETUP_PATHS=/app/example

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/supervisor

# 复制项目文件
COPY pyproject.toml README.md ./
COPY ibkr_event_daemon ./ibkr_event_daemon
COPY example ./example
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 创建日志目录
RUN mkdir -p /root/logs

# 安装项目依赖
RUN pip install --no-cache-dir -e .

# 暴露 IB Gateway 端口（如果需要）
EXPOSE 4001 4002 7496 7497

# 使用 supervisor 作为入口点
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD supervisorctl status ibkr_event_daemon | grep RUNNING || exit 1

# 添加标签
LABEL maintainer="Shawn Deng <shawndeng1109@qq.com>" \
      description="IBKR Event Daemon with FX Bar Handler support"