"""Inbound/outbound webhook delivery helpers.

Outbound delivery is intentionally best-effort: a slow or unavailable automation
provider must never prevent a Gravity event from reaching the device or app.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import hashlib
import hmac
import ipaddress
import json
import logging
import socket
from typing import Any, Awaitable, Callable, cast
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
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Webhook URL has an invalid port") from exc

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


async def ensure_public_webhook_destination(url: str) -> None:
    """Resolve a webhook hostname and reject non-public destinations before delivery."""
    normalized = validate_webhook_url(url)
    parsed = urlparse(normalized)
    hostname = parsed.hostname
    if hostname is None:  # Kept defensive for callers outside the router.
        raise ValueError("Webhook URL must include a hostname")

    loop = asyncio.get_running_loop()
    try:
        addresses = await loop.run_in_executor(
            None,
            lambda: socket.getaddrinfo(
                hostname,
                parsed.port or 443,
                type=socket.SOCK_STREAM,
            ),
        )
    except socket.gaierror as exc:
        raise ValueError("Webhook hostname could not be resolved") from exc

    if not addresses:
        raise ValueError("Webhook hostname could not be resolved")
    if any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise ValueError("Webhook hostname resolves to a private or local address")


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
    destination_validator: Callable[[str], Awaitable[None]] = ensure_public_webhook_destination,
) -> list[WebhookDelivery]:
    """POST an event to matching outbound subscriptions and record outcomes.

    Any caller changes are committed before network I/O. The webhook query
    transaction is also closed before requests begin, then delivery outcomes are
    committed separately so scheduled jobs do not silently lose status updates.
    """
    await db.commit()
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
    await db.commit()
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

    async def deliver(hook: Webhook) -> WebhookDelivery:
        hook.last_triggered_at = datetime.now(tz=timezone.utc)
        try:
            target_url = cast(str, hook.target_url)
            await destination_validator(target_url)
            response = await client.post(
                target_url,
                content=body,
                headers=signed_headers(body, hook.signing_secret),
            )
            hook.last_status = response.status_code
            if response.is_success:
                hook.last_error = ""
                return WebhookDelivery(hook.id, True, response.status_code)
            hook.last_error = f"HTTP {response.status_code}"
            return WebhookDelivery(hook.id, False, response.status_code, hook.last_error)
        except Exception as exc:
            hook.last_status = None
            hook.last_error = str(exc)[:500]
            return WebhookDelivery(hook.id, False, error=hook.last_error)

    try:
        deliveries = list(await asyncio.gather(*(deliver(hook) for hook in hooks)))
    finally:
        if owns_client:
            await client.aclose()

    await db.commit()
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
