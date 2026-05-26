"""공정 경로(Routing) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class RoutingCreate(BaseModel):
    """공정 경로 생성 요청 스키마."""

    routing_name: str
    item_code: str = ""
    operations: list[str] = Field(default_factory=list)
    total_time_minutes: Decimal = Decimal(0)


class RoutingUpdate(BaseModel):
    """공정 경로 수정 요청 스키마."""

    routing_name: str | None = None
    item_code: str | None = None
    operations: list[str] | None = None
    total_time_minutes: Decimal | None = None


class Routing(BaseDocument):
    """공정 경로 문서."""

    routing_name: str = ""
    item_code: str = ""
    operations: list[str] = Field(default_factory=list)
    total_time_minutes: Decimal = Decimal(0)
