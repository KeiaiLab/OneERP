"""부품 승인(PartApproval) 문서 모델.

신규 부품을 BOM에 등록하기 전에 기술·품질·비용 관점에서
적합성을 검증하는 부품 승인 프로세스(PAP) 문서.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class PartApprovalStatus(StrEnum):
    """부품 승인 상태."""

    REQUESTED = "requested"
    TECHNICAL_REVIEW = "technical_review"
    QUALITY_REVIEW = "quality_review"
    COST_REVIEW = "cost_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


class TechnicalReview(BaseModel):
    """기술 검토 — 임베디드 모델."""

    reviewer_id: str = ""
    result: str = "pending"
    spec_compliance: bool = False
    form_fit_function: bool = False
    reliability_assessment: str = ""
    comments: str = ""
    reviewed_at: datetime | None = None


class QualityReview(BaseModel):
    """품질 검토 — 임베디드 모델."""

    reviewer_id: str = ""
    result: str = "pending"
    incoming_inspection_plan: bool = False
    supplier_quality_rating: str = ""
    rohs_compliance: bool = False
    comments: str = ""
    reviewed_at: datetime | None = None


class CostReview(BaseModel):
    """비용 검토 — 임베디드 모델."""

    reviewer_id: str = ""
    result: str = "pending"
    unit_price: Decimal = Decimal(0)
    moq: int = 0
    lead_time_days: int = 0
    price_compared_to_current: float = 0.0
    comments: str = ""
    reviewed_at: datetime | None = None


class PartApprovalCreate(BaseModel):
    """부품 승인 생성 요청 스키마."""

    part_code: str
    part_name: str
    manufacturer: str
    manufacturer_part_number: str
    supplier_id: str | None = None
    request_reason: str
    intended_use: str
    target_products: list[str] = Field(default_factory=list)
    datasheet_url: str | None = None


class PartApprovalUpdate(BaseModel):
    """부품 승인 수정 요청 스키마."""

    part_name: str | None = None
    manufacturer: str | None = None
    manufacturer_part_number: str | None = None
    supplier_id: str | None = None
    request_reason: str | None = None
    intended_use: str | None = None
    target_products: list[str] | None = None
    datasheet_url: str | None = None


class PartApproval(BaseDocument):
    """부품 승인 문서 — PAP.

    naming prefix: PAR
    """

    part_code: str = Field(default="", description="부품 코드")
    part_name: str = Field(default="", description="부품명")
    manufacturer: str = Field(default="", description="제조사")
    manufacturer_part_number: str = Field(default="", description="제조사 부품번호")
    supplier_id: str | None = Field(default=None, description="공급사")
    status: PartApprovalStatus = Field(default=PartApprovalStatus.REQUESTED, description="상태")
    requested_by: str = Field(default="", description="요청자")
    request_reason: str = Field(default="", description="요청 사유")
    intended_use: str = Field(default="", description="사용 용도")
    target_products: list[str] = Field(default_factory=list, description="적용 예정 제품")
    technical_review: TechnicalReview | None = Field(default=None, description="기술 검토")
    quality_review: QualityReview | None = Field(default=None, description="품질 검토")
    cost_review: CostReview | None = Field(default=None, description="비용 검토")
    datasheet_url: str | None = Field(default=None, description="데이터시트 파일")
    approved_by: str | None = Field(default=None, description="최종 승인자")
    approved_at: datetime | None = Field(default=None, description="승인 시각")
    conditions: str | None = Field(default=None, description="승인 조건")
    expiry_date: date | None = Field(default=None, description="승인 만료일")
