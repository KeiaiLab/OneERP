"""감가상각(DepreciationEntry) 문서 모델 — Assets 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DepreciationEntryCreate(BaseModel):
    """감가상각 항목 생성 요청 스키마."""

    asset_ref: str
    posting_date: date | None = None
    depreciation_amount: Decimal = Decimal(0)
    accumulated_depreciation: Decimal = Decimal(0)
    remaining_value: Decimal = Decimal(0)


class DepreciationEntry(BaseDocument):
    """감가상각 항목 문서 — Assets 감가상각 관리.

    naming prefix: DEP
    """

    asset_ref: str = ""
    posting_date: date | None = None
    depreciation_amount: Decimal = Decimal(0)
    accumulated_depreciation: Decimal = Decimal(0)
    remaining_value: Decimal = Decimal(0)
