"""User-configurable inbound and outbound webhooks for IFTTT and Zapier."""

from datetime import datetime, timezone
import re
import secrets
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.models.webhook import Webhook
from backend.routers.auth import get_current_user
from backend.services.webhook_service import publish_user_event, validate_webhook_url

router = APIRouter(prefix="/integrations/webhooks", tags=["webhooks"])

EVENT_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")


class WebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    direction: Literal["inbound", "outbound"]
    event_type: str = Field(default="*")
    target_url: str | None = None
    signing_secret: str | None = Field(default=None, max_length=256)
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name must not be blank")
        return normalized

    @field_validator("event_type")
    @classmethod
    def normalize_event_type(cls, value: str) -> str:
        normalized = value.strip().upper().replace("-", "_").replace(" ", "_")
        if normalized != "*" and not EVENT_PATTERN.fullmatch(normalized):
            raise ValueError("event_type must contain only letters, numbers, and underscores")
        return normalized


class WebhookUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    event_type: str | None = None
    target_url: str | None = None
    signing_secret: str | None = Field(default=None, max_length=256)
    enabled: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("name must not be blank")
        return normalized

    @field_validator("event_type")
    @classmethod
    def normalize_event_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper().replace("-", "_").replace(" ", "_")
        if normalized != "*" and not EVENT_PATTERN.fullmatch(normalized):
            raise ValueError("event_type must contain only letters, numbers, and underscores")
        return normalized


class WebhookResponse(BaseModel):
    id: int
    name: str
    direction: str
    event_type: str
    target_url: str | None
    token: str | None
    signing_secret_configured: bool
    enabled: bool
    last_triggered_at: datetime | None
    last_status: int | None
    last_error: str
    created_at: datetime | None


class InboundTrigger(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class InboundTriggerResponse(BaseModel):
    accepted: bool = True
    event_type: str


def _to_response(hook: Webhook) -> WebhookResponse:
    return WebhookResponse(
        id=hook.id,
        name=hook.name,
        direction=hook.direction,
        event_type=hook.event_type,
        target_url=hook.target_url,
        token=hook.token if hook.direction == "inbound" else None,
        signing_secret_configured=bool(hook.signing_secret),
        enabled=hook.enabled,
        last_triggered_at=hook.last_triggered_at,
        last_status=hook.last_status,
        last_error=hook.last_error or "",
        created_at=hook.created_at,
    )


def _validate_configuration(direction: str, target_url: str | None) -> str | None:
    if direction == "outbound":
        if not target_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="target_url is required for outbound webhooks",
            )
        try:
            return validate_webhook_url(target_url)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
    if target_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="target_url is only valid for outbound webhooks",
        )
    return None


async def _owned_webhook(webhook_id: int, user_id: int, db: AsyncSession) -> Webhook:
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    hook = result.scalar_one_or_none()
    if hook is None or hook.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    return hook


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook)
        .where(Webhook.user_id == current_user.id)
        .order_by(Webhook.created_at.desc(), Webhook.id.desc())
    )
    return [_to_response(hook) for hook in result.scalars().all()]


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    req: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_url = _validate_configuration(req.direction, req.target_url)
    hook = Webhook(
        user_id=current_user.id,
        name=req.name,
        direction=req.direction,
        event_type=req.event_type,
        target_url=target_url,
        token=secrets.token_urlsafe(32) if req.direction == "inbound" else None,
        signing_secret=req.signing_secret if req.direction == "outbound" else None,
        enabled=req.enabled,
        last_error="",
    )
    db.add(hook)
    await db.flush()
    return _to_response(hook)


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    req: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hook = await _owned_webhook(webhook_id, current_user.id, db)
    changes = req.model_dump(exclude_unset=True)

    if "target_url" in changes:
        changes["target_url"] = _validate_configuration(hook.direction, changes["target_url"])
    if hook.direction == "inbound":
        changes.pop("signing_secret", None)

    for field, value in changes.items():
        setattr(hook, field, value)
    await db.flush()
    return _to_response(hook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hook = await _owned_webhook(webhook_id, current_user.id, db)
    await db.delete(hook)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/inbound/{token}",
    response_model=InboundTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_inbound_webhook(
    token: str,
    req: InboundTrigger,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook).where(
            Webhook.token == token,
            Webhook.direction == "inbound",
            Webhook.enabled.is_(True),
        )
    )
    hook = result.scalar_one_or_none()
    if hook is None or hook.direction != "inbound" or not hook.enabled or hook.token != token:
        # Deliberately return the same response for unknown and disabled tokens.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    hook.last_triggered_at = datetime.now(tz=timezone.utc)
    hook.last_status = status.HTTP_202_ACCEPTED
    hook.last_error = ""
    await publish_user_event(
        db,
        hook.user_id,
        hook.event_type,
        req.data,
    )
    return InboundTriggerResponse(event_type=hook.event_type)
