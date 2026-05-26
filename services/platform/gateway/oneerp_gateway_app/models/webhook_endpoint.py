"""웹훅 엔드포인트(WebhookEndpoint) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WebhookEndpointStatus(StrEnum):
    """웹훅 엔드포인트 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class WebhookEndpointCreate(BaseModel):
    """웹훅 엔드포인트 생성 요청 스키마."""

    endpoint_name: str
    url: str = ""
    events: list[str] = Field(default_factory=list)
    secret_key: str = ""
    is_active: bool = True


class WebhookEndpointUpdate(BaseModel):
    """웹훅 엔드포인트 수정 요청 스키마."""

    endpoint_name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    secret_key: str | None = None
    is_active: bool | None = None


class WebhookEndpoint(BaseDocument):
    """웹훅 엔드포인트 문서."""

    status: WebhookEndpointStatus = Field(
        default=WebhookEndpointStatus.ACTIVE,
        description="웹훅 엔드포인트 상태",
    )
    endpoint_name: str = ""
    url: str = ""
    events: list[str] = Field(default_factory=list)
    secret_key: str = ""
    is_active: bool = True
