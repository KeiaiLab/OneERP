"""설계 변경 지시(EngineeringChangeOrder) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class EngineeringChangeOrderStatus(StrEnum):
    """설계 변경 지시 상태."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    CANCELLED = "cancelled"


class EngineeringChangeOrderCreate(BaseModel):
    """설계 변경 지시 생성 요청 스키마."""

    change_title: str
    affected_items: list[str] = Field(default_factory=list)
    reason: str = ""
    effective_date: date | None = None


class EngineeringChangeOrderUpdate(BaseModel):
    """설계 변경 지시 수정 요청 스키마."""

    change_title: str | None = None
    affected_items: list[str] | None = None
    reason: str | None = None
    effective_date: date | None = None


class EngineeringChangeOrder(BaseDocument):
    """설계 변경 지시 문서."""

    status: EngineeringChangeOrderStatus = Field(
        default=EngineeringChangeOrderStatus.DRAFT,
        description="설계 변경 지시 상태",
    )
    change_title: str = ""
    affected_items: list[str] = Field(default_factory=list)
    reason: str = ""
    effective_date: date | None = None
