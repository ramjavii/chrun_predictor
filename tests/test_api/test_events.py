import pytest


@pytest.mark.asyncio
async def test_ingest_event(client):
    response = await client.post("/api/v1/events", json={"customer_external_id": "c1", "event_type": "login"})
    assert response.status_code == 200
