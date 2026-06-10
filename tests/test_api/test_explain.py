import pytest


@pytest.mark.asyncio
async def test_explain_customer(client):
    response = await client.get("/api/v1/explain/test-customer-id")
    assert response.status_code == 200
