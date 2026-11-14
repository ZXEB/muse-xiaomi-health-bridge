FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai \
    HOME=/home/health

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates sqlite3 tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --uid 1000 --create-home --home-dir /home/health --shell /bin/bash health

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

RUN mkdir -p /data /home/health/.mifit \
    && chown -R health:health /data /home/health

USER health
EXPOSE 8787 8788

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/healthz', timeout=3)"

CMD ["python", "-m", "health_bridge.main"]
