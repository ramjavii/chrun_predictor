FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Runtime deps
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" && \
    rm -rf /root/.cache

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS training

RUN pip install --no-cache-dir -e ".[train]" && \
    rm -rf /root/.cache

CMD ["python", "-m", "src.pipeline.train"]
