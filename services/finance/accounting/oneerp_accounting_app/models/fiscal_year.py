"""회계연도(Fiscal Year) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class FiscalYearCreate(BaseModel):
    """회계연도 생성 요청 스키마."""

    year_name: str
    start_date: date | None = None
    end_date: date | None = None
    company: str = ""
    is_closed: bool = False


class FiscalYearUpdate(BaseModel):
    """회계연도 수정 요청 스키마."""

    year_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    company: str | None = None
    is_closed: bool | None = None


class FiscalYear(BaseDocument):
    """회계연도 문서 — 회계 기간의 연 단위 구분.

    naming prefix: FY
    """

    year_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    company: str = ""
    is_closed: bool = False
