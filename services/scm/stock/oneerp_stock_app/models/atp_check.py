"""ATP 조회(AtpCheck) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AtpCheckCreate(BaseModel):
    """ATP 조회 생성 요청 스키마."""

    item_code: str
    warehouse_id: str
    requested_qty: Decimal = Decimal(0)
    available_qty: Decimal = Decimal(0)
    check_date: date | None = None
    is_available: bool = False


class AtpCheckUpdate(BaseModel):
    """ATP 조회 수정 요청 스키마."""

    item_code: str | None = None
    warehouse_id: str | None = None
    requested_qty: Decimal | None = None
    available_qty: Decimal | None = None
    check_date: date | None = None
    is_available: bool | None = None


class AtpCheck(BaseDocument):
    """ATP 조회 문서."""

    item_code: str = ""
    warehouse_id: str = ""
    requested_qty: Decimal = Decimal(0)
    available_qty: Decimal = Decimal(0)
    check_date: date | None = None
    is_available: bool = False
