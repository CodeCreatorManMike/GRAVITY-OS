from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.models.webhook import Webhook
from backend.routers import habits, webhooks


class _ScalarResult:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows if rows is not None else ([] if row is None else [row])

    def scalar_one_or_none(self):
        return self.row

    def scalars(self):
        return self

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows
        self.added = []
        self.deleted = []

    async def execute(self, _statement):
        return _ScalarResult(self.row, self.rows)

    def add(self, row):
        self.added.append(row)
        row.id = row.id or 101

    async def flush(self):
        return None

    async def delete(self, row):
        self.deleted.append(row)


def user(user_id=7):
    return SimpleNamespace(id=user_id)


@pytest.mark.asyncio
async def test_create_inbound_webhook_generates_an_unguessable_endpoint_token():
    db = FakeDB()

    created = await webhooks.create_webhook(
        webhooks.WebhookCreate(
            name="Desk plug",
            direction="inbound",
            event_type="desk_session_started",
        ),
        current_user=user(),
        db=db,
    )

    assert created.direction == "inbound"
    assert created.event_type == "DESK_SESSION_STARTED"
    assert len(created.token) >= 32
    assert created.target_url is None
    assert db.added[0].user_id == 7


@pytest.mark.asyncio
async def test_create_outbound_webhook_validates_destination_and_hides_signing_secret():
    db = FakeDB()

    with pytest.raises(HTTPException) as exc:
        await webhooks.create_webhook(
            webhooks.WebhookCreate(
                name="Unsafe",
                direction="outbound",
                event_type="HABIT_COMPLETED",
                target_url="http://localhost/admin",
            ),
            current_user=user(),
            db=db,
        )
    assert exc.value.status_code == 422

    created = await webhooks.create_webhook(
        webhooks.WebhookCreate(
            name="Zapier",
            direction="outbound",
            event_type="HABIT_COMPLETED",
            target_url="https://hooks.zapier.com/hooks/catch/123/abc",
            signing_secret="do-not-return",
        ),
        current_user=user(),
        db=db,
    )
    assert created.target_url.startswith("https://hooks.zapier.com/")
    assert created.signing_secret_configured is True
    assert not hasattr(created, "signing_secret")


@pytest.mark.asyncio
async def test_trigger_inbound_webhook_publishes_configured_event(monkeypatch):
    hook = Webhook(
        id=12,
        user_id=7,
        name="Desk plug",
        direction="inbound",
        event_type="DESK_SESSION_STARTED",
        token="inbound-token",
        enabled=True,
    )
    db = FakeDB(row=hook)
    published = []

    async def publish(db_arg, user_id, event_type, data):
        published.append((db_arg, user_id, event_type, data))
        return []

    monkeypatch.setattr(webhooks, "publish_user_event", publish)

    result = await webhooks.trigger_inbound_webhook(
        "inbound-token",
        webhooks.InboundTrigger(data={"state": "on", "source": "ifttt"}),
        db=db,
    )

    assert result.accepted is True
    assert result.event_type == "DESK_SESSION_STARTED"
    assert published == [
        (
            db,
            7,
            "DESK_SESSION_STARTED",
            {"state": "on", "source": "ifttt"},
        )
    ]
    assert hook.last_triggered_at is not None
    assert hook.last_status == 202


def test_webhook_name_cannot_be_only_whitespace():
    with pytest.raises(ValueError):
        webhooks.WebhookCreate(
            name="   ", direction="inbound", event_type="DESK_SESSION_STARTED"
        )

    with pytest.raises(ValueError):
        webhooks.WebhookUpdate(name="   ")


@pytest.mark.asyncio
async def test_trigger_rejects_unknown_or_disabled_endpoint():
    for hook in (None, Webhook(direction="inbound", enabled=False, token="disabled")):
        with pytest.raises(HTTPException) as exc:
            await webhooks.trigger_inbound_webhook(
                "missing", webhooks.InboundTrigger(data={}), db=FakeDB(row=hook)
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_and_delete_require_webhook_ownership():
    someone_elses = Webhook(id=5, user_id=99, direction="outbound", enabled=True)

    with pytest.raises(HTTPException) as update_exc:
        await webhooks.update_webhook(
            5,
            webhooks.WebhookUpdate(enabled=False),
            current_user=user(7),
            db=FakeDB(row=someone_elses),
        )
    assert update_exc.value.status_code == 404

    with pytest.raises(HTTPException) as delete_exc:
        await webhooks.delete_webhook(5, current_user=user(7), db=FakeDB(row=someone_elses))
    assert delete_exc.value.status_code == 404


@pytest.mark.asyncio
async def test_habit_completion_uses_outbound_capable_event_publisher(monkeypatch):
    habit = SimpleNamespace(id=42, user_id=7, name="Read", is_active=True, is_non_negotiable=False)

    class HabitDB:
        def __init__(self):
            self.results = [_ScalarResult(row=habit), _ScalarResult(row=None)]

        async def execute(self, _statement):
            return self.results.pop(0)

        def add(self, row):
            row.id = 1

        async def flush(self):
            return None

    published = []

    async def invalidate(*_args):
        return None

    async def publish(db_arg, user_id, event_type, data):
        published.append((db_arg, user_id, event_type, data))
        return []

    monkeypatch.setattr(habits, "invalidate_user_context", invalidate)
    monkeypatch.setattr(habits, "publish_user_event", publish, raising=False)
    db = HabitDB()

    await habits.complete_habit(42, current_user=user(), db=db)

    assert published == [
        (
            db,
            7,
            "HABIT_COMPLETED",
            {
                "habit_id": 42,
                "habit_name": "Read",
                "is_non_negotiable": False,
                "date": published[0][3]["date"],
            },
        )
    ]
