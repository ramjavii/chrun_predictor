from unittest.mock import patch

import pytest
import stripe
from sqlalchemy import select

from src.core.config import settings
from src.models.database import Event

pytestmark = pytest.mark.asyncio

_FAKE_EVENT_ID = "evt_test_123"
_FAKE_CUSTOMER = "cus_test_abc"


def _fake_stripe_event(
    stripe_type: str = "customer.subscription.created",
    customer: str = _FAKE_CUSTOMER,
    data_obj: dict | None = None,
) -> dict:
    base = {
        "id": _FAKE_EVENT_ID,
        "type": stripe_type,
        "created": 1718000000,
        "data": {
            "object": data_obj
            or {
                "id": "sub_test_456",
                "customer": customer,
                "created": 1718000000,
                "items": {"data": [{"plan": {"nickname": "pro", "amount": 2999, "interval": "month"}}]},
            }
        },
    }
    return base


async def test_returns_501_when_secret_not_configured(client):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = ""
    try:
        resp = await client.post("/api/v1/webhooks/stripe", json={})
        assert resp.status_code == 501
    finally:
        settings.stripe_webhook_secret = original


async def test_returns_400_when_missing_signature(client):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        resp = await client.post("/api/v1/webhooks/stripe", content=b"{}", headers={})
        assert resp.status_code == 400
        assert "signature" in resp.json()["detail"].lower()
    finally:
        settings.stripe_webhook_secret = original


async def test_returns_400_when_invalid_payload(client):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        with patch("stripe.Webhook.construct_event", side_effect=ValueError("bad payload")):
            resp = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"not-json",
                headers={"stripe-signature": "t=123,v1=sig"},
            )
        assert resp.status_code == 400
    finally:
        settings.stripe_webhook_secret = original


async def test_returns_400_when_invalid_signature(client):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        with patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError("bad sig", b""),
        ):
            resp = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=123,v1=bad"},
            )
        assert resp.status_code == 400
    finally:
        settings.stripe_webhook_secret = original


async def test_ignores_unsupported_event_type(client):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        event = _fake_stripe_event(stripe_type="charge.succeeded")
        with patch("stripe.Webhook.construct_event", return_value=event):
            resp = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=123,v1=sig"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"
    finally:
        settings.stripe_webhook_secret = original


async def test_ignores_event_without_customer(client):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        event = _fake_stripe_event(data_obj={"id": "sub_test_456"})
        with patch("stripe.Webhook.construct_event", return_value=event):
            resp = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=123,v1=sig"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"
        assert resp.json()["reason"] == "no_customer"
    finally:
        settings.stripe_webhook_secret = original


async def test_processes_subscription_created(client, db_session):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        event = _fake_stripe_event()
        with patch("stripe.Webhook.construct_event", return_value=event):
            resp = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=123,v1=sig"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processed"
        assert data["event_type"] == "subscription_started"
        assert data["customer_id"] == _FAKE_CUSTOMER

        events = (await db_session.execute(select(Event))).scalars().all()
        assert len(events) == 1
        assert events[0].event_type == "subscription_started"
        assert events[0].properties["stripe_event_id"] == _FAKE_EVENT_ID
        assert events[0].properties["plan"] == "pro"
        assert events[0].properties["amount"] == 2999
    finally:
        settings.stripe_webhook_secret = original


async def test_processes_subscription_cancelled(client, db_session):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        event = _fake_stripe_event(
            stripe_type="customer.subscription.deleted",
            data_obj={
                "id": "sub_test_456",
                "customer": _FAKE_CUSTOMER,
                "canceled_at": 1718000000,
                "created": 1718000000,
            },
        )
        with patch("stripe.Webhook.construct_event", return_value=event):
            resp = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=123,v1=sig"},
            )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "subscription_cancelled"

        events = (await db_session.execute(select(Event))).scalars().all()
        assert len(events) == 1
        assert events[0].event_type == "subscription_cancelled"
        assert events[0].properties["canceled_at"] == 1718000000
    finally:
        settings.stripe_webhook_secret = original


async def test_processes_payment_failed(client, db_session):
    original = settings.stripe_webhook_secret
    settings.stripe_webhook_secret = "whsec_test"
    try:
        event = _fake_stripe_event(
            stripe_type="invoice.payment_failed",
            data_obj={
                "id": "in_test_789",
                "customer": _FAKE_CUSTOMER,
                "amount_due": 2999,
                "attempt_count": 2,
                "created": 1718000000,
                "payment_intent": {
                    "last_payment_error": {
                        "code": "card_declined",
                        "message": "Your card was declined.",
                    }
                },
            },
        )
        with patch("stripe.Webhook.construct_event", return_value=event):
            resp = await client.post(
                "/api/v1/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=123,v1=sig"},
            )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "payment_failed"

        events = (await db_session.execute(select(Event))).scalars().all()
        assert len(events) == 1
        assert events[0].event_type == "payment_failed"
        assert events[0].properties["amount"] == 2999
        assert events[0].properties["attempt_count"] == 2
        assert events[0].properties["failure_code"] == "card_declined"
    finally:
        settings.stripe_webhook_secret = original
