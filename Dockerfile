# 远程打印服务 - Docker多阶段构建（精简版）

# ========== 构建阶段 ==========
FROM python:3.11-slim-bookworm AS builder

# 安装编译工具
RUN apt-get update && apt-get install -y \
    gcc \
    libcups2-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖（使用wheel加速后续构建）
COPY requirements.txt /tmp/requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt

# ========== 运行阶段 ==========
FROM python:3.11-slim-bookworm AS runner

# 只安装运行时必需的最小系统依赖
RUN apt-get update && apt-get install -y \
    cups \
    cups-client \
    cups-filters \
    ghostscript \
    poppler-utils \
    libmagic1 \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 从构建阶段复制预编译的wheel
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --find-links=/wheels -r /tmp/requirements.txt && \
    rm -rf /wheels

# 创建工作目录
WORKDIR /app

# 复制应用代码
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY requirements.txt .
COPY run.py .

# 创建必要的目录
RUN mkdir -p /app/uploads /app/logs && \
    chmod 777 /app/uploads /app/logs

# 暴露端口
EXPOSE 5000 631

# 设置CUPS配置
RUN echo "ServerName localhost" > /etc/cups/client.conf && \
    echo "Listen 631" > /etc/cups/cupsd.conf && \
    sed -i 's/Listen localhost:631/Listen 631/g' /etc/cups/cupsd.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# 启动命令
CMD ["python", "run.py"]
