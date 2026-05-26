"""예산(Budget) 문서 모델 — 워크플로우: draft → submitted → cancelled."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class BudgetItem(LineItem):
    """예산 라인 아이템 — 계정별 예산 배분."""

    account: str = Field(default="", description="계정과목")
    budget_amount: Decimal = Field(default=Decimal(0), description="예산 금액")
    actual_amount: Decimal = Field(default=Decimal(0), description="실적 금액")


class BudgetCreate(BaseModel):
    """예산 생성 요청 스키마."""

    budget_name: str = ""
    fiscal_year: str = ""
    cost_center: str = ""
    budget_amount: Decimal = Decimal(0)
    actual_amount: Decimal = Decimal(0)
    items: list[BudgetItem] = Field(default_factory=list)


class BudgetUpdate(BaseModel):
    """예산 수정 요청 스키마."""

    budget_name: str | None = None
    fiscal_year: str | None = None
    cost_center: str | None = None
    budget_amount: Decimal | None = None
    actual_amount: Decimal | None = None
    items: list[BudgetItem] | None = None


class Budget(BaseDocument):
    """예산 문서 — 회계연도/원가센터별 예산 관리.

    naming prefix: BGT
    """

    budget_name: str = Field(default="", description="예산명")
    fiscal_year: str = Field(default="", description="회계연도")
    cost_center: str = Field(default="", description="원가센터")
    budget_amount: Decimal = Field(default=Decimal(0), description="예산 총액")
    actual_amount: Decimal = Field(default=Decimal(0), description="실적 총액")
    items: list[BudgetItem] = Field(default_factory=list, description="예산 라인 아이템 목록")
