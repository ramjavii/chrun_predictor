import pytest


@pytest.mark.asyncio
async def test_predict_single(client):
    response = await client.get("/api/v1/predict/test-customer-id")
    assert response.status_code == 200
