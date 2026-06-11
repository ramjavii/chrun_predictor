import pytest


class TestGetFeatures:
    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_customer(self, client):
        resp = await client.get("/api/v1/features/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_features_after_compute(self, client, sample_customer_external_id):
        await client.post(
            "/api/v1/events",
            json={
                "customer_external_id": sample_customer_external_id,
                "event_type": "login",
            },
        )
        await client.post(
            "/api/v1/events",
            json={
                "customer_external_id": sample_customer_external_id,
                "event_type": "page_view",
                "properties": {"page": "/pricing"},
            },
        )

        compute_resp = await client.post(
            "/api/v1/features/compute",
            params={"customer_id": sample_customer_external_id},
        )
        assert compute_resp.status_code == 201
        assert compute_resp.json()["features_computed"] > 0

        get_resp = await client.get(f"/api/v1/features/{sample_customer_external_id}")
        assert get_resp.status_code == 200
        features = get_resp.json()
        assert isinstance(features, list)
        assert len(features) > 0
        assert features[0]["feature_name"] is not None
        assert features[0]["feature_value"] is not None
