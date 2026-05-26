"""소거 규칙(EliminationRule) 문서 모델.

L2 엔티티 1.3 정의를 구현한다.
내부거래 및 투자/자본 소거 규칙을 사전 정의하여 자동화한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EliminationType(StrEnum):
    """소거 유형."""

    REVENUE_EXPENSE = "revenue_expense"
    RECEIVABLE_PAYABLE = "receivable_payable"
    UNREALIZED_PROFIT_INVENTORY = "unrealized_profit_inventory"
    UNREALIZED_PROFIT_ASSET = "unrealized_profit_asset"
    DIVIDEND = "dividend"
    LOAN = "loan"
    INVESTMENT_EQUITY = "investment_equity"


class RuleStatus(StrEnum):
    """규칙 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class MatchingCriteria(BaseModel):
    """내부거래 매칭 조건."""

    source_account_pattern: str = Field(description="매도법인 계정과목 패턴")
    target_account_pattern: str = Field(description="매수법인 계정과목 패턴")
    match_by: str = Field(default="amount", description="매칭 기준 (amount/reference/both)")
    date_range_days: int = Field(default=0, description="거래일 허용 범위 (일수)")
    currency_match: bool = Field(default=True, description="통화 일치 필수 여부")


class EliminationLineTemplate(BaseModel):
    """소거 분개 라인 템플릿."""

    account_code: str = Field(description="그룹 CoA 계정과목 코드")
    entity_role: str = Field(description="법인 역할 (seller/buyer/parent/subsidiary/group)")
    amount_source: str = Field(description="금액 원천 (matched_amount/calculated/fixed)")
    amount_formula: str | None = Field(default=None, description="산출 공식")
    fixed_amount: Decimal | None = Field(default=None, description="고정 금액")


class EntityPair(BaseModel):
    """법인 쌍."""

    entity_a_id: str = Field(description="법인 A")
    entity_b_id: str = Field(description="법인 B")


class EliminationRule(BaseDocument):
    """소거 규칙 문서."""

    rule_code: str = Field(description="규칙 코드")
    rule_name: str = Field(description="규칙명")
    elimination_type: EliminationType = Field(description="소거 유형")
    description: str = Field(default="", description="규칙 설명")
    priority: int = Field(default=100, description="실행 우선순위 (낮을수록 먼저)")
    is_automatic: bool = Field(default=True, description="자동 소거 여부")
    is_recurring: bool = Field(default=True, description="반복 소거 여부")
    matching_criteria: MatchingCriteria = Field(
        default_factory=MatchingCriteria.model_construct, description="매칭 조건"
    )
    debit_entries_template: list[EliminationLineTemplate] = Field(
        default_factory=list, description="차변 분개 템플릿"
    )
    credit_entries_template: list[EliminationLineTemplate] = Field(
        default_factory=list, description="대변 분개 템플릿"
    )
    tolerance_amount: Decimal = Field(default=Decimal(1), description="허용 오차 금액")
    tolerance_percentage: Decimal = Field(default=Decimal(0), description="허용 오차 비율 (%)")
    applicable_entity_pairs: list[EntityPair] | None = Field(
        default=None, description="적용 대상 법인 쌍"
    )
    status: RuleStatus = Field(default=RuleStatus.ACTIVE, description="규칙 상태")


class EliminationRuleCreate(BaseModel):
    """소거 규칙 생성 요청 스키마."""

    rule_code: str
    rule_name: str
    elimination_type: EliminationType
    description: str = ""
    priority: int = 100
    is_automatic: bool = True
    is_recurring: bool = True
    matching_criteria: MatchingCriteria | None = None
    debit_entries_template: list[EliminationLineTemplate] = []
    credit_entries_template: list[EliminationLineTemplate] = []
    tolerance_amount: Decimal = Decimal(1)
    tolerance_percentage: Decimal = Decimal(0)
    applicable_entity_pairs: list[EntityPair] | None = None
    status: RuleStatus = RuleStatus.ACTIVE


class EliminationRuleUpdate(BaseModel):
    """소거 규칙 수정 요청 스키마."""

    rule_name: str | None = None
    description: str | None = None
    priority: int | None = None
    is_automatic: bool | None = None
    is_recurring: bool | None = None
    matching_criteria: MatchingCriteria | None = None
    debit_entries_template: list[EliminationLineTemplate] | None = None
    credit_entries_template: list[EliminationLineTemplate] | None = None
    tolerance_amount: Decimal | None = None
    tolerance_percentage: Decimal | None = None
    applicable_entity_pairs: list[EntityPair] | None = None
    status: RuleStatus | None = None
