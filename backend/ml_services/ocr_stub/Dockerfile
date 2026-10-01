FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEVICE=cpu

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ml_services/ocr_stub/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/requirements.txt

COPY ml_services/ocr_stub /app/ml_services/ocr_stub

EXPOSE 10000

CMD ["sh", "-c", "uvicorn ml_services.ocr_stub.ocr:app --host 0.0.0.0 --port ${PORT:-10000}"]
