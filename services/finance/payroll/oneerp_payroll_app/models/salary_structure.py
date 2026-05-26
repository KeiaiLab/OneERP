"""급여구조(SalaryStructure) 문서 모델 — Payroll 모듈."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SalaryComponent(BaseModel):
    """급여 구성 항목 (수당/공제)."""

    component: str = ""
    amount: Decimal = Decimal(0)
    formula: str = ""


class SalaryStructureCreate(BaseModel):
    """급여구조 생성 요청 스키마."""

    name: str
    company: str = ""
    is_active: bool = True
    earnings: list[SalaryComponent] = []
    deductions: list[SalaryComponent] = []


class SalaryStructureUpdate(BaseModel):
    """급여구조 수정 요청 스키마."""

    name: str | None = None
    company: str | None = None
    is_active: bool | None = None
    earnings: list[SalaryComponent] | None = None
    deductions: list[SalaryComponent] | None = None


class SalaryStructure(BaseDocument):
    """급여구조 문서 — Payroll 급여 체계 정의.

    naming prefix: SS
    """

    name: str = Field(default="", description="급여구조명")
    company: str = Field(default="", description="소속 회사")
    is_active: bool = Field(default=True, description="활성 여부")
    earnings: list[SalaryComponent] = Field(default_factory=list, description="수당 항목 목록")
    deductions: list[SalaryComponent] = Field(default_factory=list, description="공제 항목 목록")
