FROM python:3.11-slim

WORKDIR /srv/app

# System deps for torch + healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Pin to CPU torch (smaller image; inference is CPU-fine).
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      "torch==2.2.2" --index-url https://download.pytorch.org/whl/cpu

COPY serving/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# App code
COPY deepCommodity /srv/app/deepCommodity
COPY serving /srv/app/serving

ENV MODELS_DIR=/srv/models \
    PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/health || exit 1

CMD ["uvicorn", "serving.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
