# IDS — Churn Predictor: From Prediction to Retention

## Overview

A data-science pipeline and API that predicts customer churn using
historical behavioral data, explains why each customer is at risk,
and prescribes retention actions. Aimed at SaaS businesses that need
a pluggable churn-intelligence layer they can self-host or embed.

## Tech Stack

- **Language:** Python 3.12+
- **ML / Data:** pandas, numpy, scikit-learn, xgboost, shap, imbalanced-learn
- **API Layer:** FastAPI (async, auto-docs)
- **Orchestration:** Prefect or plain Docker Compose (ETL → train → evaluate)
- **Storage:** PostgreSQL (features, predictions, labels); MinIO (artifacts)
- **Monitoring:** Prometheus + Grafana stack for drift & performance
- **Infrastructure:** Docker Compose, Dockerfile multi-stage
- **CI/CD:** GitHub Actions (lint, test, build)

## Features

- [x] **Ingestion API** — receive customer events via REST endpoint
- [ ] **Feature Store** — time-windowed aggregations stored in PostgreSQL
- [ ] **Training Pipeline** — automated retrain on schedule or trigger
- [ ] **Prediction Endpoint** — real-time churn score for a single customer
- [ ] **Batch Predict** — score all active customers, store results
- [ ] **Explanation Module** — SHAP-based per-customer reason codes
- [ ] **Prescriptions Module** — rule-based retention action suggestions
- [ ] **Dashboard (optional)** — Streamlit or Grafana view of churn metrics
- [ ] **Drift Detection** — monitor feature & prediction drift over time
- [ ] **Docker Compose** — one-command startup of the full stack

## Implementation Stages

### Stage 1 — Core Pipeline
- Ingestion API skeleton
- Feature engineering (windowed aggregations)
- Training pipeline (train/eval/save)
- Prediction endpoint
- Docker Compose with FastAPI + PostgreSQL

### Stage 2 — Intelligence Layer
- SHAP explanations
- Prescriptions engine
- Batch scoring job
- Model registry (MinIO or filesystem)

### Stage 3 — Production Hardening
- Drift detection
- Prometheus metrics + Grafana dashboard
- CI/CD pipeline
- Load testing & performance tuning

### Stage 4 — Optional UI
- Streamlit dashboard for business users
- Admin panel for model management

## Current Stage

**Stage 1 — Core Pipeline**

## Notes & Decisions

- **Why not pickle?** Use MLflow model format or XGBoost native for
  versioning and reproducibility.
- **PostgreSQL over Redis?** Need SQL for feature queries and audit
  trails; Redis can be added later for caching.
- **SHAP over LIME?** SHAP provides game-theoretic guarantees and
  consistent explanation vectors across the model.
