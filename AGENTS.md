# IDS — Agent Instructions

## Tech Stack Enforcement

- **Language:** Python 3.12+ only. No TypeScript, no Node.js.
- **Web framework:** FastAPI with async endpoints.
- **Data layer:** pandas for EDA, SQLAlchemy 2.0 for persistence.
- **ML stack:** scikit-learn for baselines, XGBoost for production models.
- **Explainability:** SHAP for all model explanations.
- **Deployment:** Docker Compose multi-service; every service gets a `Dockerfile`.
- **Infrastructure-as-code:** Keep `docker-compose.yml` the single source of truth
  for how services connect.
- **Testing:** pytest + pytest-cov; aim for 80 %+ coverage on pipeline code.
- **Linting:** ruff for linting and formatting. Run `ruff check . && ruff format . --check`
  before every commit.

## Code Style Preferences

- Type hints on every function signature (PEP 484).
- Pydantic v2 models for all API request/response schemas.
- Functional-style transforms (pipe chains) instead of imperative loops.
- Logging via Python `logging` module, never `print()`.
- `async def` for all FastAPI route handlers and any I/O-bound function.
- Feature engineering defined declaratively in YAML config files, not hardcoded.
- Docstrings: Google style on public functions only.
- Prefer `pathlib.Path` over `os.path`.

## Error Handling Rules

- Every API route must be wrapped in a try/except or use FastAPI exception
  handlers defined in `app/core/errors.py`.
- Pipeline steps must use structured logging with `extra={"step": "...",
  "status": "..."}`.
- Database sessions must be managed via context managers (`async with
  Session()`); never leak connections.
- Model loading failures must fall back to a cached model and raise a
  warning metric, not crash the process.
- Retry transient PostgreSQL errors (deadlock, serialisation) up to 3 times
  with exponential backoff.

## Auto-Updating Docs Rule

Whenever you create a new feature, directory, API route, or pipeline step,
you must immediately update `docs/architecture.md` with a summary of the
change and an updated tree structure of the files you touched.
