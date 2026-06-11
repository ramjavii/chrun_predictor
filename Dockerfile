FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install core deps from pyproject.toml without building the package
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg \
    pydantic pydantic-settings pandas numpy \
    scikit-learn xgboost shap imbalanced-learn \
    python-multipart prometheus-client pyyaml httpx \
    pytest pytest-asyncio httpx aiosqlite ruff \
    && rm -rf /root/.cache

# Copy source and install the package itself (editable for dev)
COPY src/ src/
RUN pip install --no-cache-dir -e . && rm -rf /root/.cache

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS training

# Install training extras
RUN pip install --no-cache-dir hyperopt optuna && rm -rf /root/.cache

CMD ["python", "-m", "src.pipeline.train"]
