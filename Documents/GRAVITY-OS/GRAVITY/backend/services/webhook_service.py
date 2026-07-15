"""Inbound/outbound webhook delivery helpers.

Outbound delivery is intentionally best-effort: a slow or unavailable automation
provider must never prevent a Gravity event from reaching the device or app.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import ipaddress
import json
import logging
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.webhook import Webhook
from backend.services.connection_manager import manager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookDelivery:
    webhook_id: int
    succeeded: bool
    status_code: int | None = None
    error: str = ""


def validate_webhook_url(url: str) -> str:
    """Return a normalized public HTTPS URL or raise ValueError.

    IFTTT and Zapier both provide HTTPS endpoints. Blocking local/private hosts
    prevents a configured webhook from becoming a server-side request forgery.
    """
    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Webhook URL must be a public HTTPS URL")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Webhook URL cannot target localhost")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Webhook URL cannot target a private or local address")

    return normalized


def signed_headers(body: bytes, secret: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Gravity-Webhooks/1.0",
    }
    if secret:
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers["X-Gravity-Signature"] = f"sha256={digest}"
    return headers


async def dispatch_outbound_webhooks(
    db: AsyncSession,
    user_id: int,
    event_type: str,
    data: dict[str, Any],
    *,
    client: httpx.AsyncClient | None = None,
) -> list[WebhookDelivery]:
    """POST an event to matching outbound subscriptions and record outcomes."""
    result = await db.execute(
        select(Webhook).where(
            Webhook.user_id == user_id,
            Webhook.direction == "outbound",
            Webhook.enabled.is_(True),
            Webhook.event_type.in_([event_type, "*"]),
        ).order_by(Webhook.id.asc())
    )
    # Keep the predicate here as well as in SQL so callers using lightweight
    # repository fakes (and any future alternate store) get identical behavior.
    hooks = [
        hook
        for hook in result.scalars().all()
        if hook.user_id == user_id
        and hook.direction == "outbound"
        and hook.enabled
        and hook.event_type in (event_type, "*")
    ]
    if not hooks:
        return []

    payload = {
        "delivery_id": str(uuid4()),
        "event": event_type,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "data": data,
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(10.0), follow_redirects=False)

    deliveries: list[WebhookDelivery] = []
    try:
        for hook in hooks:
            hook.last_triggered_at = datetime.now(tz=timezone.utc)
            try:
                response = await client.post(
                    hook.target_url,
                    content=body,
                    headers=signed_headers(body, hook.signing_secret),
                )
                hook.last_status = response.status_code
                if response.is_success:
                    hook.last_error = ""
                    deliveries.append(WebhookDelivery(hook.id, True, response.status_code))
                else:
                    hook.last_error = f"HTTP {response.status_code}"
                    deliveries.append(
                        WebhookDelivery(hook.id, False, response.status_code, hook.last_error)
                    )
            except Exception as exc:
                hook.last_status = None
                hook.last_error = str(exc)[:500]
                deliveries.append(WebhookDelivery(hook.id, False, error=hook.last_error))
    finally:
        if owns_client:
            await client.aclose()

    return deliveries


async def publish_user_event(
    db: AsyncSession,
    user_id: int,
    event_type: str,
    data: dict[str, Any],
) -> list[WebhookDelivery]:
    """Publish to connected Gravity clients, then to external subscriptions."""
    await manager.send_to_user(user_id, event_type, data)
    try:
        return await dispatch_outbound_webhooks(db, user_id, event_type, data)
    except Exception:
        logger.exception("Unexpected webhook dispatch failure for user %s", user_id)
        return []
