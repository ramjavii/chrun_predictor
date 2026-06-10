# IDS — Technical Specification

*Last amended: 2026-06-10*

---

## 1. Product Layer — User Journey

### Data Scientist
1. Pushes feature definitions to a YAML config file
2. Triggers a training run via API or CLI
3. Reviews evaluation metrics (precision, recall, lift)
4. Promotes the candidate model to production

### Application (API Consumer)
1. Sends customer event → `POST /events`
2. Requests churn score → `GET /predict/{customer_id}`
3. Receives explanation → `GET /explain/{customer_id}`
4. Gets batch scores → `POST /predict/batch`

### Business User (optional Streamlit UI)
1. Logs in, sees overall churn rate trending
2. Drills into a segment, sees top drivers
3. Exports a list of at-risk customers with suggested actions

---

## 2. Technical Layer — Hard Constraints

| Layer         | Choice                   | Rationale                              |
|---------------|--------------------------|----------------------------------------|
| Language      | Python 3.12              | ML ecosystem, async support            |
| Web framework | FastAPI                  | Auto OpenAPI, async, Pydantic validation |
| ORM           | SQLAlchemy 2.0 + Alembic | Mature, async sessions                 |
| ML framework  | scikit-learn + XGBoost   | Tabular data baseline + SOTA boosting  |
| Explainer     | SHAP                     | Consistent additive feature attribution |
| Task runner   | Prefect 3 (optional)     | DAG retries, observability             |
| Containers    | Docker Compose           | Portable dev & prod environment        |
| Monitoring    | Prometheus + Grafana     | Industry standard, native FastAPI      |

---

## 3. Database Schema Drafts

### `customers`
| Column       | Type         | Notes                         |
|--------------|--------------|-------------------------------|
| id           | UUID PK      |                               |
| external_id  | VARCHAR(255) | client-side identifier        |
| created_at   | TIMESTAMPTZ  |                               |
| updated_at   | TIMESTAMPTZ  |                               |
| is_active    | BOOLEAN      | soft-delete flag              |

### `events`
| Column       | Type         | Notes                         |
|--------------|--------------|-------------------------------|
| id           | BIGSERIAL PK |                               |
| customer_id  | UUID FK      |                               |
| event_type   | VARCHAR(128) | e.g. `login`, `page_view`     |
| properties   | JSONB        | arbitrary event payload       |
| timestamp    | TIMESTAMPTZ  | event time (not ingest time)  |

### `features`
| Column       | Type         | Notes                         |
|--------------|--------------|-------------------------------|
| id           | BIGSERIAL PK |                               |
| customer_id  | UUID FK      |                               |
| feature_name | VARCHAR(128) |                               |
| feature_value| FLOAT        |                               |
| window_start | TIMESTAMPTZ  | start of aggregation window   |
| window_end   | TIMESTAMPTZ  | end of aggregation window     |
| computed_at  | TIMESTAMPTZ  | when the feature was computed |

### `predictions`
| Column       | Type         | Notes                         |
|--------------|--------------|-------------------------------|
| id           | BIGSERIAL PK |                               |
| customer_id  | UUID FK      |                               |
| model_version| VARCHAR(64)  | link to model registry        |
| score        | FLOAT        | churn probability [0,1]       |
| threshold    | FLOAT        | decision threshold used       |
| predicted_label| BOOLEAN    | churn / no churn              |
| created_at   | TIMESTAMPTZ  |                               |

### `explanations`
| Column       | Type         | Notes                         |
|--------------|--------------|-------------------------------|
| id           | BIGSERIAL PK |                               |
| prediction_id| BIGINT FK    |                               |
| feature_name | VARCHAR(128) |                               |
| shap_value   | FLOAT        | signed contribution           |

### `model_metadata`
| Column       | Type         | Notes                         |
|--------------|--------------|-------------------------------|
| version      | VARCHAR(64) PK | semver or hash               |
| artifact_path| VARCHAR(512) | local or S3 path              |
| metrics      | JSONB        | {precision, recall, f1, auc}  |
| trained_at   | TIMESTAMPTZ  |                               |
| status       | VARCHAR(32)  | staging / production / archived |

---

## 4. API Routes & Endpoints

| Method | Path                | Description                       |
|--------|---------------------|-----------------------------------|
| POST   | `/api/v1/events`    | Ingest a single customer event    |
| POST   | `/api/v1/events/batch` | Ingest multiple events         |
| GET    | `/api/v1/predict/{customer_id}` | Real-time churn score |
| POST   | `/api/v1/predict/batch` | Score all active customers    |
| GET    | `/api/v1/explain/{customer_id}` | SHAP values for a customer |
| GET    | `/api/v1/models`    | List registered models            |
| POST   | `/api/v1/models/register` | Register a trained model     |
| POST   | `/api/v1/train`     | Trigger a training run            |
| GET    | `/api/v1/metrics`   | Prometheus metrics endpoint       |
| GET    | `/health`           | Health check                      |

---

## 5. UI/UX Component Hierarchy (Streamlit Dashboard — optional)

```
Dashboard
├── Sidebar
│   ├── Date range picker
│   ├── Segment filter
│   └── Model version selector
├── Overview Page
│   ├── ChurnRateCard (KPI)
│   ├── AtRiskCountCard (KPI)
│   └── ChurnTrendChart (line)
├── Customers Page
│   ├── CustomerTable (sortable, searchable)
│   └── CustomerDetailModal
│       ├── ScoreGauge
│       ├── ShapWaterfall (plotly)
│       └── PrescriptionList
└── Models Page
    ├── ModelComparisonTable
    └── DriftReportChart
```

---

## 6. Edge Cases & Race Conditions

1. **Duplicate events** — idempotency key (`event.idempotency_key`)
   prevents double-counting.
2. **Cold-start customers** — default feature vector = median of
   population; flag `is_cold_start` in prediction response.
3. **Stale features** — feature computation must check `window_end`
   staleness; if > 2× window, recompute or mark as `stale`.
4. **Training / scoring race** — a training run that deletes old
   features while a scoring request reads them → use read-committed
   isolation or a feature snapshot table.
5. **Model drift during serving** — if drift score > threshold,
   route predictions to a fallback (last known good model) and alert.

---

## 7. Security Notes

- **API auth** — bearer token via `X-API-Key` header; validated
  against a secrets manager or env var.
- **Rate limiting** — `slowapi` middleware on `/predict` endpoints.
- **Input validation** — Pydantic models reject malformed events at
  the boundary.
- **Secrets** — never logged; `.env` files git-ignored; production
  secrets via Docker secrets or Vault.
- **Model artifacts** — scan pickle/joblib files with a size limit
  (e.g. 2 GB) before loading; prefer XGBoost native format.
- **SQL injection** — SQLAlchemy parameterised queries throughout.
- **CORS** — locked to known origins in production.
