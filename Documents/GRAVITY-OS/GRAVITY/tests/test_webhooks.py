import hashlib
import hmac
import json

import httpx
import pytest

from backend.models.webhook import Webhook
from backend.services import webhook_service


class _Scalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _Scalars(self._rows)


class FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.commits = 0

    async def execute(self, _statement):
        return _Result(self.rows)

    async def commit(self):
        self.commits += 1


async def allow_destination(_url):
    return None


@pytest.mark.parametrize(
    "url",
    [
        "http://hooks.zapier.com/hooks/catch/123/abc",
        "ftp://hooks.zapier.com/hook",
        "https://localhost/hook",
        "https://127.0.0.1/hook",
        "https://10.0.0.8/hook",
    ],
)
def test_validate_webhook_url_rejects_unsafe_destinations(url):
    with pytest.raises(ValueError):
        webhook_service.validate_webhook_url(url)


def test_validate_webhook_url_accepts_public_https_destination():
    assert (
        webhook_service.validate_webhook_url("https://hooks.zapier.com/hooks/catch/123/abc")
        == "https://hooks.zapier.com/hooks/catch/123/abc"
    )


def test_signed_headers_use_exact_request_body():
    body = b'{"event":"HABIT_COMPLETED"}'

    headers = webhook_service.signed_headers(body, "top-secret")

    expected = hmac.new(b"top-secret", body, hashlib.sha256).hexdigest()
    assert headers["X-Gravity-Signature"] == f"sha256={expected}"
    assert headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_dispatch_sends_matching_enabled_webhooks_and_records_success():
    matching = Webhook(
        id=1,
        user_id=7,
        name="Zapier habit log",
        direction="outbound",
        event_type="HABIT_COMPLETED",
        target_url="https://hooks.zapier.com/hook",
        signing_secret="secret",
        enabled=True,
    )
    wildcard = Webhook(
        id=2,
        user_id=7,
        name="IFTTT all events",
        direction="outbound",
        event_type="*",
        target_url="https://maker.ifttt.com/trigger/all",
        enabled=True,
    )
    ignored = Webhook(
        id=3,
        user_id=7,
        name="Disabled",
        direction="outbound",
        event_type="HABIT_COMPLETED",
        target_url="https://example.com/hook",
        enabled=False,
    )
    requests = []

    async def handler(request: httpx.Request):
        requests.append(request)
        return httpx.Response(202)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        db = FakeDB([matching, wildcard, ignored])
        deliveries = await webhook_service.dispatch_outbound_webhooks(
            db,
            user_id=7,
            event_type="HABIT_COMPLETED",
            data={"habit_id": 42, "habit_name": "Read"},
            client=client,
            destination_validator=allow_destination,
        )

    assert len(requests) == 2
    assert [delivery.webhook_id for delivery in deliveries] == [1, 2]
    assert all(delivery.succeeded for delivery in deliveries)
    payload = json.loads(requests[0].content)
    assert payload["event"] == "HABIT_COMPLETED"
    assert payload["data"] == {"habit_id": 42, "habit_name": "Read"}
    assert payload["delivery_id"]
    assert payload["created_at"].endswith("+00:00")
    assert matching.last_status == 202
    assert matching.last_error == ""
    assert matching.last_triggered_at is not None
    assert ignored.last_triggered_at is None
    assert db.commits == 3


@pytest.mark.asyncio
async def test_dispatch_is_best_effort_and_records_failure():
    hook = Webhook(
        id=9,
        user_id=7,
        name="Broken hook",
        direction="outbound",
        event_type="NUDGE",
        target_url="https://example.com/hook",
        enabled=True,
    )

    async def handler(_request: httpx.Request):
        raise httpx.ConnectError("connection refused")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        deliveries = await webhook_service.dispatch_outbound_webhooks(
            FakeDB([hook]),
            7,
            "NUDGE",
            {"message": "Stand up"},
            client=client,
            destination_validator=allow_destination,
        )

    assert deliveries[0].succeeded is False
    assert hook.last_status is None
    assert "connection refused" in hook.last_error
    assert hook.last_triggered_at is not None


@pytest.mark.asyncio
async def test_publish_user_event_reaches_websocket_even_when_outbound_fails(monkeypatch):
    sent = []

    class FakeManager:
        async def send_to_user(self, user_id, event_type, data):
            sent.append((user_id, event_type, data))

    async def fail_dispatch(*_args, **_kwargs):
        raise RuntimeError("unexpected dispatcher failure")

    monkeypatch.setattr(webhook_service, "manager", FakeManager())
    monkeypatch.setattr(webhook_service, "dispatch_outbound_webhooks", fail_dispatch)

    deliveries = await webhook_service.publish_user_event(
        FakeDB([]), 7, "HABIT_COMPLETED", {"habit_id": 42}
    )

    assert sent == [(7, "HABIT_COMPLETED", {"habit_id": 42})]
    assert deliveries == []


@pytest.mark.asyncio
async def test_destination_validation_rejects_hostname_resolving_to_private_ip(monkeypatch):
    def private_result(*_args, **_kwargs):
        return [(None, None, None, None, ("127.0.0.1", 443))]

    monkeypatch.setattr(webhook_service.socket, "getaddrinfo", private_result)

    with pytest.raises(ValueError, match="private or local"):
        await webhook_service.ensure_public_webhook_destination("https://internal.example/hook")


def test_validate_webhook_url_rejects_invalid_port():
    with pytest.raises(ValueError, match="invalid port"):
        webhook_service.validate_webhook_url("https://hooks.zapier.com:not-a-port/hook")
