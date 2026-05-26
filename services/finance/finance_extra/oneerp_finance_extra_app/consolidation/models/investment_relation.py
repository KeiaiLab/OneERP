"""투자 관계(InvestmentRelation) 문서 모델.

L2 엔티티 1.2 정의를 구현한다.
법인 간 지분 관계, 영업권, 연결 방법 자동 판단 데이터를 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

from .consolidation_entity import ConsolidationMethod

if TYPE_CHECKING:
    from datetime import date


class RelationStatus(StrEnum):
    """투자 관계 상태."""

    ACTIVE = "active"
    DISPOSED = "disposed"
    PENDING = "pending"


class InvestmentRelation(BaseDocument):
    """투자 관계 문서."""

    investor_entity_id: str = Field(description="투자자 법인 ID")
    investee_entity_id: str = Field(description="피투자자 법인 ID")
    ownership_percentage: Decimal = Field(default=Decimal(0), description="소유 지분율 (%)")
    voting_rights_percentage: Decimal = Field(default=Decimal(0), description="의결권 비율 (%)")
    effective_ownership_percentage: Decimal | None = Field(
        default=None, description="유효 지분율 (간접 지분 포함)"
    )
    acquisition_date: date = Field(description="취득일")
    acquisition_cost: Decimal = Field(default=Decimal(0), description="취득 대가")
    acquisition_cost_currency: str = Field(default="KRW", description="취득 대가 통화")
    fair_value_net_assets: Decimal | None = Field(
        default=None, description="취득 시점 순자산 공정가치"
    )
    goodwill: Decimal | None = Field(default=None, description="영업권")
    nci_fair_value: Decimal | None = Field(default=None, description="취득 시점 NCI 공정가치")
    consolidation_method: ConsolidationMethod = Field(
        default=ConsolidationMethod.FULL, description="연결 방법"
    )
    is_control: bool = Field(default=False, description="지배력 보유 여부")
    is_significant_influence: bool = Field(default=False, description="유의적 영향력 여부")
    is_joint_control: bool = Field(default=False, description="공동지배력 여부")
    disposal_date: date | None = Field(default=None, description="처분일")
    disposal_proceeds: Decimal | None = Field(default=None, description="처분 대가")
    status: RelationStatus = Field(default=RelationStatus.ACTIVE, description="관계 상태")
    remarks: str = Field(default="", description="비고")


class InvestmentRelationCreate(BaseModel):
    """투자 관계 생성 요청 스키마."""

    investor_entity_id: str
    investee_entity_id: str
    ownership_percentage: Decimal = Decimal(0)
    voting_rights_percentage: Decimal = Decimal(0)
    acquisition_date: date
    acquisition_cost: Decimal = Decimal(0)
    acquisition_cost_currency: str = "KRW"
    fair_value_net_assets: Decimal | None = None
    nci_fair_value: Decimal | None = None
    is_joint_control: bool = False
    disposal_date: date | None = None
    disposal_proceeds: Decimal | None = None
    remarks: str = ""


class InvestmentRelationUpdate(BaseModel):
    """투자 관계 수정 요청 스키마."""

    ownership_percentage: Decimal | None = None
    voting_rights_percentage: Decimal | None = None
    fair_value_net_assets: Decimal | None = None
    nci_fair_value: Decimal | None = None
    is_joint_control: bool | None = None
    disposal_date: date | None = None
    disposal_proceeds: Decimal | None = None
    status: RelationStatus | None = None
    remarks: str | None = None
