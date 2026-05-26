"""휴가잔액(LeaveBalance) 문서 모델 — HR 모듈 (Report)."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LeaveBalance(BaseDocument):
    """휴가잔액 — HR 휴가잔액 집계 뷰."""

    employee: str = ""
    leave_type: str = ""
    fiscal_year: str = ""
    expiry_date: date | None = None
    total_allocated: Decimal = Decimal(0)
    total_used: Decimal = Decimal(0)
    allocated_days: Decimal = Decimal(0)
    used_days: Decimal = Decimal(0)
    balance: Decimal = Decimal(0)


class LeaveBalanceCreate(BaseModel):
    """휴가잔액 생성 스키마."""

    employee: str
    leave_type: str
    fiscal_year: str = ""
    expiry_date: date | None = None
    total_allocated: Decimal = Decimal(0)
    total_used: Decimal = Decimal(0)
    allocated_days: Decimal = Decimal(0)
    used_days: Decimal = Decimal(0)
    balance: Decimal = Decimal(0)


class LeaveBalanceUpdate(BaseModel):
    """휴가잔액 수정 스키마."""

    employee: str | None = None
    leave_type: str | None = None
    fiscal_year: str | None = None
    expiry_date: date | None = None
    total_allocated: Decimal | None = None
    total_used: Decimal | None = None
    allocated_days: Decimal | None = None
    used_days: Decimal | None = None
    balance: Decimal | None = None
