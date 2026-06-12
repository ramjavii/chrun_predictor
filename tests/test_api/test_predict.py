import pytest


@pytest.mark.asyncio
async def test_predict_returns_null_when_no_model(client, sample_customer_external_id):
    resp = await client.get(f"/api/v1/predict/{sample_customer_external_id}")
    assert resp.status_code == 200
    assert resp.json()["score"] is None


@pytest.mark.asyncio
async def test_predict_after_training(client):
    # Seed events via API, then compute features, then train, then predict
    ingest_resp = await client.post(
        "/api/v1/events",
        json={
            "customer_external_id": "predict-c1",
            "event_type": "page_view",
            "timestamp": "2026-06-01T00:00:00Z",
            "properties": {"page": "/pricing"},
        },
    )
    assert ingest_resp.status_code == 201

    compute_resp = await client.post(
        "/api/v1/features/compute?customer_id=predict-c1",
    )
    assert compute_resp.status_code == 201

    train_resp = await client.post("/api/v1/train")
    assert train_resp.status_code == 200
    data = train_resp.json()
    assert data["status"] == "ok"
    assert data["metrics"]["n_samples"] == 1

    predict_resp = await client.get("/api/v1/predict/predict-c1")
    assert predict_resp.status_code == 200
    result = predict_resp.json()
    assert result["score"] is not None
    assert isinstance(result["score"], float)
    assert "predicted_label" in result
