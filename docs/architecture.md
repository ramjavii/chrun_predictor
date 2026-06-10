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
│   │   ├── test_predict.py
│   │   └── test_explain.py
│   ├── test_pipeline/
│   │   ├── test_features.py
│   │   └── test_train.py
│   └── test_explainer/
│       └── test_shap.py
└── data/
    ├── raw/                        # Raw input data (gitignored)
    ├── processed/                  # Feature-engineered data (gitignored)
    └── models/                     # Trained artifacts (gitignored)
```
