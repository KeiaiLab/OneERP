"""급여항목(SalaryComponent) 문서 모델 — Payroll 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SalaryComponentCreate(BaseModel):
    """급여항목 생성 요청 스키마."""

    component_name: str
    component_type: str = "earning"
    is_tax_applicable: bool = False
    description: str = ""


class SalaryComponentUpdate(BaseModel):
    """급여항목 수정 요청 스키마."""

    component_name: str | None = None
    component_type: str | None = None
    is_tax_applicable: bool | None = None
    description: str | None = None


class SalaryComponent(BaseDocument):
    """급여항목 문서 — Payroll 급여항목 마스터.

    naming prefix: SCMP
    """

    component_name: str = ""
    component_type: str = "earning"
    is_tax_applicable: bool = False
    description: str = ""
