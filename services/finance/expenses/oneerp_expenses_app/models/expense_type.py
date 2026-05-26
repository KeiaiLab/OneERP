"""경비유형(ExpenseType) 문서 모델 — Expenses 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ExpenseTypeCreate(BaseModel):
    """경비유형 생성 요청 스키마."""

    expense_type_name: str
    account: str = ""
    description: str = ""
    is_active: bool = True


class ExpenseTypeUpdate(BaseModel):
    """경비유형 수정 요청 스키마."""

    expense_type_name: str | None = None
    account: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ExpenseType(BaseDocument):
    """경비유형 문서 — Expenses 경비유형 마스터.

    naming prefix: EXT
    """

    expense_type_name: str = Field(default="", description="경비유형명")
    account: str = Field(default="", description="연결 계정과목")
    description: str = Field(default="", description="설명")
    is_active: bool = Field(default=True, description="활성 여부")
