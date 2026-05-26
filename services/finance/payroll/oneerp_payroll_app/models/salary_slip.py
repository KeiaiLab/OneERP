"""급여명세(SalarySlip) 문서 모델 — Payroll 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

from .salary_structure import SalaryComponent  # noqa: TC001  # Pydantic 런타임 필요


class SalarySlipCreate(BaseModel):
    """급여명세 생성 요청 스키마."""

    employee_id: str
    employee_name: str = ""
    salary_structure_ref: str = ""
    payroll_entry_id: str = ""
    posting_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    gross_pay: Decimal = Decimal(0)
    total_deduction: Decimal = Decimal(0)
    net_pay: Decimal = Decimal(0)
    earnings: list[SalaryComponent] = []
    deductions: list[SalaryComponent] = []


class SalarySlip(BaseDocument):
    """급여명세 문서 — Payroll 급여 지급 내역.

    naming prefix: SLIP
    """

    employee_id: str = Field(default="", description="직원 ID")
    employee_name: str = Field(default="", description="직원명")
    salary_structure_ref: str = Field(default="", description="급여구조 참조 ID")
    payroll_entry_id: str = Field(default="", description="급여대장 참조 ID")
    posting_date: date | None = Field(default=None, description="전기일자")
    start_date: date | None = Field(default=None, description="급여 시작일")
    end_date: date | None = Field(default=None, description="급여 종료일")
    gross_pay: Decimal = Field(default=Decimal(0), description="총 지급액")
    total_deduction: Decimal = Field(default=Decimal(0), description="총 공제액")
    net_pay: Decimal = Field(default=Decimal(0), description="실수령액")
    earnings: list[SalaryComponent] = Field(default_factory=list, description="수당 항목 목록")
    deductions: list[SalaryComponent] = Field(default_factory=list, description="공제 항목 목록")
