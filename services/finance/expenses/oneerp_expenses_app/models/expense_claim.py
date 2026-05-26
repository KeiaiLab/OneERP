"""경비청구(ExpenseClaim) 문서 모델 — Expenses 모듈.

L2 비즈니스 룰 매핑:
- BR-EXP-008: Draft만 수정/취소 가능
- BR-EXP-013: 경비 항목 합계 = 총 금액
- BR-EXP-014: 가맹점 정보 기록
- BR-EXP-015: 감사 추적
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from typing import Any

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field, model_validator


class ExpenseClaimItem(LineItem):
    """경비청구 항목."""

    expense_type: str = ""
    amount: Decimal = Decimal(0)
    description: str = ""
    expense_date: date | None = None


class ExpenseClaimCreate(BaseModel):
    """경비청구 생성 요청 스키마.

    E2E 흐름에서 사용하는 필드:
    - employee_id, employee_name, posting_date
    - expense_type_id: 경비유형 참조
    - expenses: 간편 항목 목록 (ExpenseClaimItem로 변환)
    - total_claimed_amount: 총 청구 금액
    - items: 기존 라인아이템 (직접 지정 시)
    """

    employee_id: str
    employee_name: str = ""
    posting_date: date | None = None
    expense_type_id: str = ""
    total_amount: Decimal = Decimal(0)
    total_claimed_amount: Decimal = Decimal(0)
    approval_status: str = "pending"
    items: list[dict[str, Any]] = Field(default_factory=list)
    expenses: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _항목합계_동기화(self) -> ExpenseClaimCreate:
        """BR-EXP-013: 경비 항목 합계와 total_amount를 동기화한다."""
        if self.items:
            items_total = sum((Decimal(str(i.get("amount", 0))) for i in self.items), Decimal(0))
            if self.total_amount == 0:
                self.total_amount = items_total
            if self.total_claimed_amount == 0:
                self.total_claimed_amount = items_total
        return self


class ExpenseClaimUpdate(BaseModel):
    """경비청구 수정 요청 스키마."""

    employee_id: str | None = None
    employee_name: str | None = None
    posting_date: date | None = None
    expense_type_id: str | None = None
    total_amount: Decimal | None = None
    total_claimed_amount: Decimal | None = None
    approval_status: str | None = None
    items: list[dict[str, Any]] | None = None
    expenses: list[dict[str, Any]] | None = None


class ExpenseClaim(BaseDocument):
    """경비청구 문서 — Expenses 경비 트랜잭션.

    naming prefix: EXP
    """

    employee_id: str = Field(default="", alias="employee", description="직원 ID")
    employee_name: str = Field(default="", description="직원명")
    posting_date: date | None = Field(default=None, description="전기일자")
    expense_type_id: str = Field(default="", description="경비유형 참조 ID")
    total_amount: Decimal = Field(default=Decimal(0), description="총 청구 금액 (레거시)")
    total_claimed_amount: Decimal = Field(default=Decimal(0), description="총 청구 금액")
    approval_status: str = Field(default="pending", description="승인 상태")
    items: list[dict[str, Any]] = Field(default_factory=list, description="경비 항목 목록")
    expenses: list[dict[str, Any]] = Field(default_factory=list, description="간편 경비 항목 목록")
