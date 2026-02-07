# 远程打印服务 - Docker配置

# Python基础镜像
FROM python:3.11-slim-bookworm

# 维护者信息
LABEL maintainer="Remote Print Service"
LABEL description="Remote Print Service with CUPS integration"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    cups \
    cups-client \
    cups-filters \
    hpijs-ppds \
    hplip \
    ghostscript \
    poppler-utils \
    libmagic1 \
    fonts-dejavu-core \
    fonts-liberation \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

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
    echo "Listen 631" >> /etc/cups/cupsd.conf && \
    sed -i 's/Listen localhost:631/Listen 631/g' /etc/cups/cupsd.conf && \
    sed -i 's/BrowseAddress @LOCAL/BrowseAddress 127.0.0.1:631/g' /etc/cups/cupsd.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# 启动命令
CMD ["python", "run.py"]
