# ========== 构建阶段：只打 wheels（更快、更稳） ==========
FROM python:3.11-slim-bookworm AS builder
WORKDIR /build

COPY requirements.txt /tmp/requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt


# ========== 运行阶段 ==========
FROM python:3.11-slim-bookworm AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 运行时系统依赖：
# - python3-cups: 提供 import cups
# - cups/cups-filters/ghostscript/poppler-utils: 打印与格式处理
# - weasyprint 运行库：cairo/pango/gdk-pixbuf 等
# - supervisor: 同时拉起 cupsd + 你的服务
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-cups libcups2 \
    cups cups-client cups-filters \
    ghostscript poppler-utils \
    libmagic1 \
    fonts-dejavu-core fonts-liberation \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi8 libjpeg62-turbo zlib1g libglib2.0-0 shared-mime-info \
    supervisor \
 && rm -rf /var/lib/apt/lists/*

# 关键：让 /usr/local/bin/python(官方镜像) 也能加载 Debian dist-packages（cups 模块在这里）
RUN python - <<'PY'
import site, os
sp = site.getsitepackages()[0]
with open(os.path.join(sp, "debian-dist-packages.pth"), "w") as f:
    f.write("/usr/lib/python3/dist-packages\n")
    f.write("/usr/lib/python3.11/dist-packages\n")
PY

# 安装 Python 依赖（离线 wheels）
COPY requirements.txt /tmp/requirements.txt
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt \
 && rm -rf /wheels /tmp/requirements.txt

# 应用代码
WORKDIR /app
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run.py .

RUN mkdir -p /app/uploads /app/logs && chmod 777 /app/uploads /app/logs

# CUPS 基础配置：允许容器内监听 631
# 注意：不要用 echo > 覆盖整个 cupsd.conf，这里用 sed 修改默认配置更安全
RUN sed -i 's/^\(Listen\).*/Listen 0.0.0.0:631/' /etc/cups/cupsd.conf || true \
 && grep -q '^Port 631' /etc/cups/cupsd.conf || echo 'Port 631' >> /etc/cups/cupsd.conf \
 && echo "ServerName localhost" > /etc/cups/client.conf

# Supervisor 配置：同时启动 cupsd + 你的服务
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5000 631

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

CMD ["supervisord", "-n"]