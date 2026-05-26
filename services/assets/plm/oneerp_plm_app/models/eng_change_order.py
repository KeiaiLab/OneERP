"""설계 변경 요청(ECO) 문서 모델.

제품/부품의 설계 변경을 공식 요청하고 다부서 검토·승인을 거치는 변경 관리 문서.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class ChangeType(StrEnum):
    """변경 유형."""

    DESIGN = "design"
    PROCESS = "process"
    MATERIAL = "material"
    COST_REDUCTION = "cost_reduction"
    QUALITY = "quality"
    SAFETY = "safety"
    REGULATORY = "regulatory"


class Priority(StrEnum):
    """우선순위."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ECOStatus(StrEnum):
    """ECO 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    CANCELLED = "cancelled"


# ECO 상태 전이 규칙
ECO_TRANSITIONS: dict[ECOStatus, list[ECOStatus]] = {
    ECOStatus.DRAFT: [ECOStatus.SUBMITTED],
    ECOStatus.SUBMITTED: [ECOStatus.IN_REVIEW, ECOStatus.CANCELLED],
    ECOStatus.IN_REVIEW: [ECOStatus.APPROVED, ECOStatus.REJECTED],
    ECOStatus.APPROVED: [ECOStatus.IMPLEMENTED, ECOStatus.CANCELLED],
    ECOStatus.REJECTED: [ECOStatus.DRAFT],
    ECOStatus.IMPLEMENTED: [],
    ECOStatus.CANCELLED: [],
}


class ProposedChange(BaseModel):
    """제안 변경 — 임베디드 모델."""

    change_target_type: str = Field(
        description="변경 대상 유형 (bom/drawing/part/process/certification)"
    )
    change_target_id: str = Field(description="변경 대상 엔티티 ID")
    change_description: str = Field(description="변경 내용 설명")
    before_value: str = Field(default="", description="변경 전 값")
    after_value: str = Field(default="", description="변경 후 값")


class ImpactAnalysis(BaseModel):
    """영향도 분석 — 임베디드 모델."""

    affected_bom_count: int = 0
    affected_drawing_count: int = 0
    affected_certification_count: int = 0
    affected_work_order_count: int = 0
    affected_stock_value: Decimal = Decimal(0)
    risk_level: str = "low"
    analysis_notes: str = ""
    analyzed_at: datetime | None = None


class CostImpact(BaseModel):
    """비용 영향 — 임베디드 모델."""

    material_cost_delta: Decimal = Decimal(0)
    tooling_cost: Decimal = Decimal(0)
    certification_cost: Decimal = Decimal(0)
    scrap_cost: Decimal = Decimal(0)
    total_cost_impact: Decimal = Decimal(0)
    payback_period_months: int | None = None


class Reviewer(BaseModel):
    """검토자 — 임베디드 모델."""

    reviewer_id: str = Field(description="검토자 사용자 ID")
    reviewer_name: str = Field(default="", description="검토자명")
    review_role: str = Field(
        description="검토 역할 (design/production/quality/purchasing/management)"
    )
    review_status: str = Field(default="pending", description="검토 상태")
    review_comment: str = Field(default="", description="검토 의견")
    reviewed_at: datetime | None = Field(default=None, description="검토 시각")


class ECOCreate(BaseModel):
    """ECO 생성 요청 스키마."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    change_type: ChangeType
    priority: Priority = Priority.MEDIUM
    is_emergency: bool = False
    affected_products: list[str] = Field(min_length=1)
    affected_bom_versions: list[str] = Field(default_factory=list)
    proposed_changes: list[ProposedChange] = Field(min_length=1)
    cost_impact: CostImpact | None = None
    target_effective_date: date | None = None


class ECOUpdate(BaseModel):
    """ECO 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    change_type: ChangeType | None = None
    priority: Priority | None = None
    is_emergency: bool | None = None
    affected_products: list[str] | None = None
    proposed_changes: list[ProposedChange] | None = None
    cost_impact: CostImpact | None = None
    target_effective_date: date | None = None


class EngChangeOrder(BaseDocument):
    """설계 변경 요청 문서 — ECO.

    naming prefix: ECO
    """

    eco_number: str = Field(default="", description="ECO 번호")
    title: str = Field(default="", description="변경 제목")
    description: str = Field(default="", description="변경 사유 및 상세 내용")
    change_type: ChangeType = Field(default=ChangeType.DESIGN, description="변경 유형")
    priority: Priority = Field(default=Priority.MEDIUM, description="우선순위")
    status: ECOStatus = Field(default=ECOStatus.DRAFT, description="상태")
    is_emergency: bool = Field(default=False, description="긴급 ECO 여부")
    requested_by: str = Field(default="", description="요청자")
    assigned_to: str | None = Field(default=None, description="담당자")
    affected_products: list[str] = Field(default_factory=list, description="영향 받는 제품")
    affected_bom_versions: list[str] = Field(default_factory=list, description="영향 받는 BOM")
    affected_drawings: list[str] = Field(default_factory=list, description="영향 받는 도면")
    affected_certifications: list[str] = Field(default_factory=list, description="영향 받는 인증")
    impact_analysis: ImpactAnalysis | None = Field(default=None, description="영향도 분석 결과")
    proposed_changes: list[ProposedChange] = Field(
        default_factory=list, description="제안 변경 목록"
    )
    cost_impact: CostImpact | None = Field(default=None, description="비용 영향")
    reviewers: list[Reviewer] = Field(default_factory=list, description="검토자 목록")
    target_effective_date: date | None = Field(default=None, description="목표 적용일")
    actual_effective_date: date | None = Field(default=None, description="실제 적용일")
    ecn_id: str | None = Field(default=None, description="생성된 ECN ID")
    submitted_at: datetime | None = Field(default=None, description="제출 시각")
    approved_at: datetime | None = Field(default=None, description="승인 시각")
    approved_by: str | None = Field(default=None, description="승인자")
    implemented_at: datetime | None = Field(default=None, description="적용 완료 시각")
