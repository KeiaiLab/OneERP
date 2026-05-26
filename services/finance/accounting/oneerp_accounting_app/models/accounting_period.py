"""회계기간(Accounting Period) 문서 모델 — 마스터 데이터."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AccountingPeriodCreate(BaseModel):
    """회계기간 생성 요청 스키마."""

    period_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    company: str = ""
    status: str = "open"
    fiscal_year: str = ""


class AccountingPeriodUpdate(BaseModel):
    """회계기간 수정 요청 스키마."""

    period_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    company: str | None = None
    status: str | None = None
    fiscal_year: str | None = None


class AccountingPeriod(BaseDocument):
    """회계기간 문서 — 회계 마감/개시 기간 관리.

    naming prefix: APD
    """

    period_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    company: str = ""
    status: str = "open"
    fiscal_year: str = ""
