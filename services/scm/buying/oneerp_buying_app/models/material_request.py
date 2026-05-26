"""자재요청(Material Request) 문서 모델."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class MaterialRequestItem(LineItem):
    """자재요청 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    warehouse: str = Field(default="", description="대상 창고")
    required_date: date | None = Field(default=None, description="필요일자")
    item_group: str = Field(default="", description="품목 그룹")
    estimated_unit_cost: Decimal = Field(default=Decimal(0), description="예상 단가")
    estimated_amount: Decimal = Field(default=Decimal(0), description="예상 금액")
    suggested_supplier_id: str = Field(default="", description="추천 공급업체 ID")
    suggested_supplier_name: str = Field(default="", description="추천 공급업체명")
    suggestion_source: str = Field(default="", description="추천 근거")


class MaterialRequestCreate(BaseModel):
    """자재요청 생성 요청 스키마."""

    request_type: str = "purchase"
    required_date: date | None = None
    budget_limit: Decimal = Decimal(0)
    items: list[MaterialRequestItem] = []


class MaterialRequestUpdate(BaseModel):
    """자재요청 수정 요청 스키마."""

    request_type: str | None = None
    required_date: date | None = None
    budget_limit: Decimal | None = None
    items: list[MaterialRequestItem] | None = None


class MaterialRequestCreateRFQ(BaseModel):
    """자재요청 기반 RFQ 생성 요청."""

    suppliers: list[str]
    transaction_date: date | None = None


class MaterialRequest(BaseDocument):
    """자재요청 문서 — 구매/이전/제조를 위한 자재 요청.

    naming prefix: MR
    """

    request_type: str = Field(
        default="purchase", description="요청 유형 (purchase / transfer / manufacture)"
    )
    required_date: date | None = Field(default=None, description="필요일자")
    items: list[MaterialRequestItem] = Field(
        default_factory=list, description="자재요청 라인 아이템 목록"
    )
    total_qty: Decimal = Field(default=Decimal(0), description="총 요청 수량")
    estimated_total_amount: Decimal = Field(default=Decimal(0), description="총 예상 구매 금액")
    budget_limit: Decimal = Field(default=Decimal(0), description="구매 요청 예산 한도")
    budget_status: str = Field(default="unchecked", description="예산 상태")
    approval_status: str = Field(default="not_required", description="승인 상태")
    required_approver: str = Field(default="", description="결재자")
    approval_matrix_id: str = Field(default="", description="적용 승인 매트릭스")
    approval_requested_by: str = Field(default="", description="승인 요청자")
    approved_by: str = Field(default="", description="승인자")
    approved_at: datetime | None = Field(default=None, description="승인 시각")
    rejected_by: str = Field(default="", description="반려자")
    rejected_reason: str = Field(default="", description="반려 사유")
    suggested_supplier_id: str = Field(default="", description="대표 추천 공급업체 ID")
    suggested_supplier_name: str = Field(default="", description="대표 추천 공급업체명")
