"""연결 대상 법인(ConsolidationEntity) 문서 모델.

L2 엔티티 1.1 정의를 Pydantic v2 모델로 구현한다.
법인 유형, 연결 방법, 기능통화 등을 관리한다.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class EntityType(StrEnum):
    """법인 유형."""

    PARENT = "parent"
    SUBSIDIARY = "subsidiary"
    ASSOCIATE = "associate"
    JOINT_VENTURE = "joint_venture"


class ConsolidationMethod(StrEnum):
    """연결 방법."""

    FULL = "full"
    EQUITY = "equity"
    PROPORTIONATE = "proportionate"
    NONE = "none"


class EntityStatus(StrEnum):
    """법인 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class ConsolidationEntity(BaseDocument):
    """연결 대상 법인 문서."""

    entity_code: str = Field(description="법인 코드")
    entity_name: str = Field(description="법인명")
    entity_type: EntityType = Field(default=EntityType.SUBSIDIARY, description="법인 유형")
    country_code: str = Field(default="KR", description="소재 국가 (ISO 3166-1 alpha-2)")
    functional_currency: str = Field(default="KRW", description="기능통화 (ISO 4217)")
    consolidation_method: ConsolidationMethod = Field(
        default=ConsolidationMethod.FULL, description="연결 방법"
    )
    is_parent: bool = Field(default=False, description="지배기업 여부")
    accounting_entity_id: str | None = Field(default=None, description="개별 회계 법인 연결 ID")
    fiscal_year_start_month: int = Field(default=1, description="회계연도 시작월")
    chart_of_accounts_mapping_id: str | None = Field(default=None, description="그룹 CoA 매핑 참조")
    sub_group_id: str | None = Field(default=None, description="소속 중간 지주회사")
    status: EntityStatus = Field(default=EntityStatus.ACTIVE, description="법인 상태")
    acquisition_date: date | None = Field(default=None, description="취득일")
    disposal_date: date | None = Field(default=None, description="처분일")
    remarks: str = Field(default="", description="비고")


class ConsolidationEntityCreate(BaseModel):
    """법인 생성 요청 스키마."""

    entity_code: str
    entity_name: str
    entity_type: EntityType = EntityType.SUBSIDIARY
    country_code: str = "KR"
    functional_currency: str = "KRW"
    consolidation_method: ConsolidationMethod = ConsolidationMethod.FULL
    is_parent: bool = False
    accounting_entity_id: str | None = None
    fiscal_year_start_month: int = 1
    chart_of_accounts_mapping_id: str | None = None
    sub_group_id: str | None = None
    status: EntityStatus = EntityStatus.ACTIVE
    acquisition_date: date | None = None
    disposal_date: date | None = None
    remarks: str = ""


class ConsolidationEntityUpdate(BaseModel):
    """법인 수정 요청 스키마."""

    entity_name: str | None = None
    entity_type: EntityType | None = None
    country_code: str | None = None
    functional_currency: str | None = None
    consolidation_method: ConsolidationMethod | None = None
    is_parent: bool | None = None
    accounting_entity_id: str | None = None
    fiscal_year_start_month: int | None = None
    chart_of_accounts_mapping_id: str | None = None
    sub_group_id: str | None = None
    status: EntityStatus | None = None
    acquisition_date: date | None = None
    disposal_date: date | None = None
    remarks: str | None = None
