"""보증 기간(WarrantyPeriod) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class WarrantyPeriodCreate(BaseModel):
    """보증 기간 생성 요청 스키마."""

    item_code: str
    warranty_months: int = 12
    start_date: date | None = None
    end_date: date | None = None
    terms: str = ""


class WarrantyPeriodUpdate(BaseModel):
    """보증 기간 수정 요청 스키마."""

    item_code: str | None = None
    warranty_months: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    terms: str | None = None


class WarrantyPeriod(BaseDocument):
    """보증 기간 문서."""

    item_code: str = ""
    warranty_months: int = 12
    start_date: date | None = None
    end_date: date | None = None
    terms: str = ""
