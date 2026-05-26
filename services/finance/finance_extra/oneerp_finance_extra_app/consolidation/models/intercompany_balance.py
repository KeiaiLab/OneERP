"""내부거래 잔액(IntercompanyBalance) 문서 모델.

L2 엔티티 1.7 정의를 구현한다.
법인 간 내부거래 잔액 집계 및 양방향 대사 데이터를 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class IntercompanyBalanceType(StrEnum):
    """내부거래 잔액 유형."""

    REVENUE_EXPENSE = "revenue_expense"
    RECEIVABLE_PAYABLE = "receivable_payable"
    LOAN = "loan"
    DIVIDEND = "dividend"
    OTHER = "other"


class MatchStatus(StrEnum):
    """대사 상태."""

    UNMATCHED = "unmatched"
    MATCHED = "matched"
    WITHIN_TOLERANCE = "within_tolerance"
    MISMATCH = "mismatch"


class IntercompanyBalance(BaseDocument):
    """내부거래 잔액 문서."""

    period_id: str = Field(description="연결 기간")
    entity_a_id: str = Field(description="법인 A (매도/대여/배당지급)")
    entity_b_id: str = Field(description="법인 B (매수/차입/배당수취)")
    balance_type: IntercompanyBalanceType = Field(description="잔액 유형")
    entity_a_amount: Decimal = Field(default=Decimal(0), description="법인 A 장부 금액")
    entity_a_currency: str = Field(default="KRW", description="법인 A 통화")
    entity_a_account_code: str = Field(default="", description="법인 A 계정과목")
    entity_b_amount: Decimal = Field(default=Decimal(0), description="법인 B 장부 금액")
    entity_b_currency: str = Field(default="KRW", description="법인 B 통화")
    entity_b_account_code: str = Field(default="", description="법인 B 계정과목")
    entity_a_translated_amount: Decimal | None = Field(
        default=None, description="법인 A 보고통화 환산액"
    )
    entity_b_translated_amount: Decimal | None = Field(
        default=None, description="법인 B 보고통화 환산액"
    )
    difference_amount: Decimal = Field(default=Decimal(0), description="차이 금액")
    difference_percentage: Decimal = Field(default=Decimal(0), description="차이 비율 (%)")
    match_status: MatchStatus = Field(default=MatchStatus.UNMATCHED, description="대사 상태")
    tolerance_applied: Decimal | None = Field(default=None, description="적용된 허용 오차")
    elimination_entry_id: str | None = Field(default=None, description="연결된 소거 전표 ID")
    source_journal_ids_a: list[str] = Field(
        default_factory=list, description="법인 A 원천 전표 ID 목록"
    )
    source_journal_ids_b: list[str] = Field(
        default_factory=list, description="법인 B 원천 전표 ID 목록"
    )
    remarks: str = Field(default="", description="비고")


class IntercompanyBalanceCreate(BaseModel):
    """내부거래 잔액 생성 요청 스키마."""

    period_id: str
    entity_a_id: str
    entity_b_id: str
    balance_type: IntercompanyBalanceType
    entity_a_amount: Decimal = Decimal(0)
    entity_a_currency: str = "KRW"
    entity_a_account_code: str = ""
    entity_b_amount: Decimal = Decimal(0)
    entity_b_currency: str = "KRW"
    entity_b_account_code: str = ""
    remarks: str = ""


class IntercompanyBalanceUpdate(BaseModel):
    """내부거래 잔액 수정 요청 스키마."""

    entity_a_amount: Decimal | None = None
    entity_b_amount: Decimal | None = None
    match_status: MatchStatus | None = None
    remarks: str | None = None
