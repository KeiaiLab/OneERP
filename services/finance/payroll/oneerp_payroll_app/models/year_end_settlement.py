"""연말정산(YearEndSettlement) 문서 모델 — Payroll 모듈."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class YearEndDeductions(BaseModel):
    """연말정산 소득공제 항목."""

    earned_income_deduction: Decimal = Field(default=Decimal(0), description="근로소득공제")
    personal_deduction: Decimal = Field(default=Decimal(0), description="인적공제")
    pension_deduction: Decimal = Field(default=Decimal(0), description="연금보험료 공제")
    special_deduction: Decimal = Field(default=Decimal(0), description="특별소득공제")
    other_deduction: Decimal = Field(default=Decimal(0), description="기타 공제")
    total: Decimal = Field(default=Decimal(0), description="소득공제 합계")


class YearEndCredits(BaseModel):
    """연말정산 세액공제 항목."""

    earned_income_credit: Decimal = Field(default=Decimal(0), description="근로소득 세액공제")
    child_credit: Decimal = Field(default=Decimal(0), description="자녀 세액공제")
    pension_savings_credit: Decimal = Field(default=Decimal(0), description="연금저축 세액공제")
    insurance_credit: Decimal = Field(default=Decimal(0), description="보장성보험료 세액공제")
    other_credit: Decimal = Field(default=Decimal(0), description="기타 세액공제")
    total: Decimal = Field(default=Decimal(0), description="세액공제 합계")


class YearEndSettlementCreate(BaseModel):
    """연말정산 생성 요청 스키마."""

    fiscal_year: str
    employee: str
    employee_name: str = ""
    total_income: Decimal = Decimal(0)
    total_tax: Decimal = Decimal(0)
    settlement_amount: Decimal = Decimal(0)
    deductions: YearEndDeductions = Field(default_factory=YearEndDeductions)
    credits: YearEndCredits = Field(default_factory=YearEndCredits)
    taxable_income: Decimal = Decimal(0)
    calculated_tax: Decimal = Decimal(0)
    tax_paid: Decimal = Decimal(0)


class YearEndSettlementUpdate(BaseModel):
    """연말정산 수정 요청 스키마."""

    fiscal_year: str | None = None
    employee: str | None = None
    employee_name: str | None = None
    total_income: Decimal | None = None
    total_tax: Decimal | None = None
    settlement_amount: Decimal | None = None
    deductions: YearEndDeductions | None = None
    credits: YearEndCredits | None = None
    taxable_income: Decimal | None = None
    calculated_tax: Decimal | None = None
    tax_paid: Decimal | None = None


class YearEndSettlement(BaseDocument):
    """연말정산 문서 — Payroll 연말정산 트랜잭션.

    naming prefix: YES
    """

    fiscal_year: str = ""
    employee: str = ""
    employee_name: str = ""
    total_income: Decimal = Decimal(0)
    total_tax: Decimal = Decimal(0)
    settlement_amount: Decimal = Decimal(0)
    deductions: YearEndDeductions = Field(default_factory=YearEndDeductions)
    credits: YearEndCredits = Field(default_factory=YearEndCredits)
    taxable_income: Decimal = Field(default=Decimal(0), description="과세표준")
    calculated_tax: Decimal = Field(default=Decimal(0), description="산출세액")
    tax_paid: Decimal = Field(default=Decimal(0), description="기납부세액")
