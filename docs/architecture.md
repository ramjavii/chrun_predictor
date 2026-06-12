# IDS — Architecture Overview

## Project Tree

```
IDS/
├── MVP.md                          # Product roadmap & stages
├── spec.md                         # Technical specification
├── AGENTS.md                       # Agent coding rules
├── opencode.json                   # opencode configuration
├── .gitignore
├── .env.example
├── pyproject.toml                  # Project metadata & dependencies
├── Dockerfile                      # API service image
├── docker-compose.yml              # Multi-service orchestration
├── requirements/
│   ├── base.txt                    # Core runtime deps
│   ├── dev.txt                     # Dev/test/lint deps
│   └── train.txt                   # Training-only deps
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Settings from env
│   │   ├── database.py             # Engine & session factories
│   │   ├── errors.py               # Exception handlers
│   │   └── logging.py              # Logging configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── events.py               # POST /events
│   │   ├── predict.py              # GET /predict/{id}, POST /predict/batch
│   │   ├── features.py             # GET /features/{id}, POST /features/compute
│   │   ├── explain.py              # GET /explain/{id}
│   │   ├── models.py               # GET /models, POST /models/register
│   │   └── train.py                # POST /train
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py             # SQLAlchemy ORM models
│   │   └── schemas.py              # Pydantic request/response schemas
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── features.py             # Feature engineering transforms
│   │   ├── feature_store.py        # DB-backed compute orchestration
│   │   ├── train.py                # Training orchestration
│   │   ├── evaluate.py             # Metrics computation
│   │   └── predict.py              # Batch & real-time scoring
│   ├── explainer/
│   │   ├── __init__.py
│   │   └── shap_explainer.py       # SHAP explanation engine
│   └── prescriptions/
│       ├── __init__.py
│       └── engine.py               # Rule-based action suggestions
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures (test DB, test client)
│   ├── test_api/
│   │   ├── test_events.py
│   │   ├── test_feature_store.py
│   │   └── test_predict.py
│   └── test_pipeline/
│       ├── test_feature_transforms.py
│       └── test_train.py
└── data/
    ├── raw/                        # Raw input data (gitignored)
    ├── processed/                  # Feature-engineered data (gitignored)
    └── models/                     # Trained artifacts (gitignored)
```

## Changelog

### 2026-06-10 — Ingestion API (Stage 1)
- Implemented `POST /api/v1/events` and `POST /api/v1/events/batch`
- Added `init_db()` auto-creates tables on startup via FastAPI lifespan
- Refactored `src/models/database.py`: fixed `TIMESTAMPTZ` → `TIMESTAMP(timezone=True)`, deprecated `utcnow` → `datetime.now(UTC)`
- Added response schemas `EventResponse` and `EventBatchResponse` to `src/models/schemas.py`
- Tests: session-scoped event loop, in-memory conftest with `prepare_db` fixture
- Added `ruff` to dev deps, configured `ignore = ["B008"]` for FastAPI `Depends()`
- Renamed `IDSException` → `IDSError` (ruff N818)
- Pinned all deps via pip install in Dockerfile

### 2026-06-10 — Feature Store (Stage 1)
- Implemented `_count_events`, `_recency_days`, `_avg_time_between_events` transforms in `src/pipeline/features.py`
- Created `configs/features.yaml` with declarative transform definitions
- Created `src/pipeline/feature_store.py`: reads events from DB, computes features per YAML config, writes to `features` table
- Created `GET /api/v1/features/{customer_id}` and `POST /api/v1/features/compute?customer_id=...`
- Added `FeatureResponse` schema to `src/models/schemas.py`
- 16/16 tests passing (pipeline unit tests + API integration tests)

### 2026-06-11 — Training Pipeline & Prediction Endpoint (Stage 1)
- Implemented `src/pipeline/train.py`: `build_training_dataset()` loads feature pivots from DB, heuristic churn labels (90 days inactivity), trains XGBoost, saves JSON artifact to `/data/models/`
- Implemented `src/pipeline/predict.py`: `predict_single()` loads latest production model, builds feature vector aligned to model's expected columns, returns churn probability
- Created `POST /api/v1/train` endpoint in `src/api/train.py`
- Created `GET /api/v1/predict/{customer_id}` and `POST /api/v1/predict/batch` in `src/api/predict.py`
- Added `ModelMetadata` and `Prediction` ORM models to `src/models/database.py`
- Added `ModelRegisterRequest` and `PredictionResponse` schemas to `src/models/schemas.py`
- Fixed feature alignment between train and predict: sorted `feature_cols` during training so order matches `_get_feature_vector` (alphabetical by name)
- Fixed `db_session` fixture isolation: use `test_engine.begin()` for TRUNCATE instead of session-level commit to prevent rollback on session close
- 17/17 tests passing
