import pytest


class TestIngestEvent:
    @pytest.mark.asyncio
    async def test_creates_event_and_returns_201(self, client, sample_customer_external_id):
        payload = {
            "customer_external_id": sample_customer_external_id,
            "event_type": "page_view",
            "properties": {"page": "/pricing"},
        }
        resp = await client.post("/api/v1/events", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["event_type"] == "page_view"
        assert body["customer_external_id"] == sample_customer_external_id
        assert "id" in body

    @pytest.mark.asyncio
    async def test_creates_customer_automatically(self, client, sample_customer_external_id):
        payload = {
            "customer_external_id": sample_customer_external_id,
            "event_type": "login",
        }
        resp = await client.post("/api/v1/events", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["customer_external_id"] == sample_customer_external_id

    @pytest.mark.asyncio
    async def test_rejects_missing_event_type(self, client):
        resp = await client.post("/api/v1/events", json={"customer_external_id": "c1"})
        assert resp.status_code == 422


class TestIngestEventBatch:
    @pytest.mark.asyncio
    async def test_creates_multiple_events(self, client, sample_customer_external_id):
        payload = [
            {
                "customer_external_id": sample_customer_external_id,
                "event_type": "login",
            },
            {
                "customer_external_id": sample_customer_external_id,
                "event_type": "page_view",
                "properties": {"page": "/home"},
            },
        ]
        resp = await client.post("/api/v1/events/batch", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert len(body["events"]) == 2
        assert body["events"][0]["event_type"] == "login"
        assert body["events"][1]["event_type"] == "page_view"
