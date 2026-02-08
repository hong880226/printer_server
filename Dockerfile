# ========== 构建阶段：编译 pycups ==========
FROM python:3.11-slim-bookworm AS builder

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libcups2-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 先安装需要编译的 pycups
RUN pip install --no-cache-dir pycups>=2.0.1

# 再打包其他依赖为 wheels
COPY requirements.txt /tmp/requirements.txt
RUN grep -v 'pycups' /tmp/requirements.txt > /tmp/requirements_no_cups.txt && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements_no_cups.txt


# ========== 运行阶段 ==========
FROM python:3.11-slim-bookworm AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 运行时代码依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi8 libjpeg62-turbo zlib1g libglib2.0-0 shared-mime-info \
    libmagic1 \
    fonts-dejavu-core fonts-liberation \
    supervisor \
 && rm -rf /var/lib/apt/lists/*

# 让官方 Python 能加载 Debian dist-packages
RUN python - <<'PY'
import site, os
sp = site.getsitepackages()[0]
with open(os.path.join(sp, "debian-dist-packages.pth"), "w") as f:
    f.write("/usr/lib/python3/dist-packages\n")
    f.write("/usr/lib/python3.11/dist-packages\n")
PY

# 复制并安装依赖
COPY requirements.txt /tmp/requirements.txt
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt \
 && rm -rf /wheels /tmp/requirements.txt

# 应用代码
WORKDIR /app
COPY backend/ ./backend/
COPY frontend/templates/ ./backend/templates/
COPY frontend/static/ ./frontend/static/
COPY run.py .

RUN mkdir -p /app/uploads /app/logs && chmod 777 /app/uploads /app/logs

# Supervisor 配置
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

CMD ["supervisord", "-n"]
