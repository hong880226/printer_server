FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      supervisor \
      # cups: 提供 import cups（稳定，不用 pip 编译 pycups）
      python3-cups \
      libcups2 \
      cups-client \
      # python-magic: 运行时需要 libmagic + magic database
      libmagic1 \
      file \
      # pdf2image: 需要 pdftoppm/pdftocairo
      poppler-utils \
      # weasyprint 运行依赖（尽量精简）
      libcairo2 \
      libpango-1.0-0 \
      libpangocairo-1.0-0 \
      libgdk-pixbuf-2.0-0 \
      libglib2.0-0 \
      libffi8 \
      libjpeg62-turbo \
      zlib1g \
      shared-mime-info \
      # 基础字体
      fonts-dejavu-core \
    ; \
    rm -rf /var/lib/apt/lists/*

# 让 /usr/local 的 Python 能加载 Debian dist-packages（python3-cups 在这里）
RUN python - <<'PY'
import site, os
sp = site.getsitepackages()[0]
with open(os.path.join(sp, "debian-dist-packages.pth"), "w") as f:
    f.write("/usr/lib/python3/dist-packages\n")
    f.write("/usr/lib/python3.11/dist-packages\n")
PY

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

# 构建期校验，避免上线才炸
RUN python -c "import cups, magic; print('cups/magic ok')" \
 && command -v pdftoppm >/dev/null \
 && command -v pdftocairo >/dev/null

WORKDIR /app
COPY backend/ ./backend/
COPY frontend/templates/ ./backend/templates/
COPY frontend/static/ ./frontend/static/
COPY run.py .

RUN mkdir -p /app/uploads /app/logs /app/uploads/previews \
 && chmod 777 /app/uploads /app/logs /app/uploads/previews

RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

CMD ["supervisord", "-n"]