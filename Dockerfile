# 使用官方 Python 3.12 精简版镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 创建配置目录
RUN mkdir -p /app/data

# 声明挂载点
VOLUME ["/app/data"]

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/supervisor

# 复制项目文件
COPY . .

# 安装项目依赖
RUN pip install -e .

# 使用 supervisor 作为入口点
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD supervisorctl status ibkr_event_daemon | grep RUNNING || exit 1

# 添加标签
LABEL maintainer="Shawn Deng <shawndeng1109@qq.com>" \
      description="IBKR Event Daemon with FX Bar Handler support" \
      usage.volume="挂载数据目录：docker run -v /path/to/data:/app/data ..." \
      usage.env="环境变量配置：docker run -e VARIABLE=value ..."