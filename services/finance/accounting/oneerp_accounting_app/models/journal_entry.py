"""분개전표(Journal Entry) 문서 모델.

L2 엔티티 정의를 Pydantic v2 모델로 구현한다.

L2 검증 규칙:
- BR-ACCT-001: 차대변 합계 일치 (Decimal, 허용오차 1e-9)
- BR-ACCT-002: 최소 라인 수 ≥ 2
"""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field, model_validator

# 금액 비교 허용 오차 — 부동소수점 변환 시 미세 차이 허용
_TOLERANCE = Decimal("0.000000001")


def _validate_balanced_items(items: list[JournalEntryItem] | None) -> None:
    """분개 라인 공통 검증을 수행한다."""
    if items is None:
        return
    if len(items) < 2:
        msg = "분개전표는 최소 2개 이상의 라인 아이템이 필요합니다"
        raise ValueError(msg)
    total_debit = sum(item.debit for item in items)
    total_credit = sum(item.credit for item in items)
    if abs(total_debit - total_credit) > _TOLERANCE:
        msg = f"차변 합계({total_debit})와 대변 합계({total_credit})가 일치하지 않습니다"
        raise ValueError(msg)


class JournalEntryItem(LineItem):
    """분개전표 라인 아이템 — 개별 차변/대변 항목."""

    account: str = Field(description="계정과목")
    account_type: str = Field(
        default="", description="계정 유형 (asset/liability/equity/income/expense)"
    )
    debit: Decimal = Field(default=Decimal(0), description="차변 금액")
    credit: Decimal = Field(default=Decimal(0), description="대변 금액")
    cost_center: str | None = Field(default=None, description="원가센터")


class JournalEntryApprovalRequest(BaseModel):
    """분개전표 승인 요청 스키마."""

    approver: str = Field(min_length=1, description="결재자 사용자 ID")
    comment: str = Field(default="", description="승인 요청 코멘트")


class JournalEntryRejectRequest(BaseModel):
    """분개전표 반려 요청 스키마."""

    reason: str = Field(min_length=1, description="반려 사유")


class JournalEntryTemplateCreate(BaseModel):
    """반복 전표 템플릿 생성 스키마."""

    template_name: str = Field(min_length=1, description="템플릿명")
    description: str = ""
    voucher_type: str = "journal_entry"
    recurrence_unit: str = Field(
        default="monthly", description="daily/weekly/monthly/quarterly/yearly"
    )
    interval: int = Field(default=1, ge=1, description="반복 간격")
    next_posting_date: date | None = None
    items: list[JournalEntryItem] = []
    remark: str = ""
    default_approver: str = ""

    @model_validator(mode="after")
    def _템플릿_라인_검증(self) -> JournalEntryTemplateCreate:
        _validate_balanced_items(self.items)
        return self


class JournalEntryTemplateInstantiate(BaseModel):
    """반복 전표 템플릿으로 분개 초안을 생성하는 요청."""

    posting_date: date
    remark: str | None = None
    required_approver: str | None = None


class JournalEntry(BaseDocument):
    """분개전표 문서 — 복식부기 기반 회계 기록의 기본 단위.

    naming prefix: JE
    """

    posting_date: date | None = Field(default=None, description="전기일자")
    voucher_type: str = Field(default="journal_entry", description="전표 유형")
    voucher_no: str = Field(default="", description="원본 전표 번호 (자동 분개 시 설정)")
    total_debit: Decimal = Field(default=Decimal(0), description="차변 합계")
    total_credit: Decimal = Field(default=Decimal(0), description="대변 합계")
    items: list[JournalEntryItem] = Field(default_factory=list, description="분개 라인 아이템 목록")
    remark: str = Field(default="", description="적요")
    approval_required: bool = Field(default=False, description="승인 필요 여부")
    approval_status: str = Field(
        default="not_requested",
        description="not_requested/pending/approved/rejected/not_required",
    )
    required_approver: str = Field(default="", description="지정 결재자")
    approval_requested_by: str = Field(default="", description="승인 요청자")
    approval_requested_at: datetime | None = Field(default=None, description="승인 요청 시각")
    approval_comment: str = Field(default="", description="승인 요청 메모")
    approved_by: str = Field(default="", description="승인자")
    approved_at: datetime | None = Field(default=None, description="승인 시각")
    rejected_by: str = Field(default="", description="반려자")
    rejected_at: datetime | None = Field(default=None, description="반려 시각")
    rejection_reason: str = Field(default="", description="반려 사유")
    template_id: str = Field(default="", description="원본 반복 전표 템플릿 ID")


class JournalEntryTemplate(BaseDocument):
    """반복 전표 템플릿 문서."""

    template_name: str = ""
    description: str = ""
    voucher_type: str = "journal_entry"
    recurrence_unit: str = "monthly"
    interval: int = 1
    next_posting_date: date | None = None
    items: list[JournalEntryItem] = Field(default_factory=list, description="반복 전표 라인")
    remark: str = ""
    default_approver: str = ""
    usage_count: int = 0
