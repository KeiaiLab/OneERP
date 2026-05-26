"""연결 재무제표(ConsolidatedReport) 문서 모델.

L2 엔티티 1.5 정의를 구현한다.
연결 결산 결과물인 BS, PL, CF, SOCE 보고서를 저장한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class ReportType(StrEnum):
    """보고서 유형."""

    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    EQUITY_CHANGES = "equity_changes"


class ReportStatus(StrEnum):
    """보고서 상태."""

    DRAFT = "draft"
    FINAL = "final"
    SUPERSEDED = "superseded"


class ReportLineItem(BaseModel):
    """보고서 라인 항목."""

    line_no: int = Field(description="라인 순서")
    account_code: str = Field(description="그룹 CoA 계정 코드")
    account_name: str = Field(description="계정과목명")
    account_level: int = Field(default=1, description="계정 깊이")
    is_subtotal: bool = Field(default=False, description="소계 여부")
    current_period: Decimal = Field(default=Decimal(0), description="당기 금액")
    prior_period: Decimal | None = Field(default=None, description="전기 금액")
    variance: Decimal | None = Field(default=None, description="변동액")
    variance_percentage: Decimal | None = Field(default=None, description="변동률 (%)")
    parent_controlling: Decimal | None = Field(default=None, description="지배기업 귀속분")
    nci: Decimal | None = Field(default=None, description="비지배지분 귀속분")


class EntityBreakdown(BaseModel):
    """법인별 내역."""

    entity_id: str = Field(description="CENT ID")
    entity_name: str = Field(description="법인명")
    functional_currency: str = Field(description="기능통화")
    original_amount: Decimal = Field(default=Decimal(0), description="원통화 금액")
    translated_amount: Decimal = Field(default=Decimal(0), description="환산 후 금액")
    translation_rate: Decimal | None = Field(default=None, description="적용 환율")
    account_code: str = Field(description="계정 코드")


class EliminationBreakdown(BaseModel):
    """소거 내역."""

    elimination_type: str = Field(description="소거 유형")
    rule_id: str = Field(description="소거 규칙 ID")
    amount: Decimal = Field(default=Decimal(0), description="소거 금액")
    account_code: str = Field(description="계정 코드")
    debit_entity_id: str | None = Field(default=None, description="차변 법인")
    credit_entity_id: str | None = Field(default=None, description="대변 법인")


class NCIEntityDetail(BaseModel):
    """법인별 NCI 상세."""

    entity_id: str = Field(description="CENT ID")
    entity_name: str = Field(description="법인명")
    nci_percentage: Decimal = Field(default=Decimal(0), description="NCI 비율 (%)")
    nci_equity: Decimal = Field(default=Decimal(0), description="NCI 자본")
    nci_profit: Decimal = Field(default=Decimal(0), description="NCI 귀속 당기순이익")
    nci_oci: Decimal | None = Field(default=None, description="NCI 귀속 OCI")


class NCIBreakdown(BaseModel):
    """비지배지분 내역."""

    total_nci_equity: Decimal = Field(default=Decimal(0), description="NCI 자본 합계")
    total_nci_profit: Decimal = Field(default=Decimal(0), description="NCI 귀속 당기순이익")
    total_nci_oci: Decimal | None = Field(default=None, description="NCI 귀속 OCI")
    entity_details: list[NCIEntityDetail] = Field(
        default_factory=list, description="법인별 NCI 상세"
    )


class ReportTotals(BaseModel):
    """합계."""

    total_assets: Decimal | None = Field(default=None, description="총자산 (BS)")
    total_liabilities: Decimal | None = Field(default=None, description="총부채 (BS)")
    total_equity: Decimal | None = Field(default=None, description="총자본 (BS)")
    parent_equity: Decimal | None = Field(default=None, description="지배기업 귀속 자본")
    nci_equity: Decimal | None = Field(default=None, description="비지배지분")
    total_revenue: Decimal | None = Field(default=None, description="총매출 (PL)")
    total_expense: Decimal | None = Field(default=None, description="총비용 (PL)")
    net_income: Decimal | None = Field(default=None, description="당기순이익 (PL)")
    parent_net_income: Decimal | None = Field(default=None, description="지배기업 귀속 순이익")
    nci_net_income: Decimal | None = Field(default=None, description="NCI 귀속 순이익")
    net_cash_operating: Decimal | None = Field(default=None, description="영업활동 현금흐름 (CF)")
    net_cash_investing: Decimal | None = Field(default=None, description="투자활동 현금흐름 (CF)")
    net_cash_financing: Decimal | None = Field(default=None, description="재무활동 현금흐름 (CF)")
    bs_balance_check: Decimal | None = Field(default=None, description="BS 균형 검증 (0이어야 함)")


class ConsolidatedReport(BaseDocument):
    """연결 재무제표 문서."""

    period_id: str = Field(description="연결 기간 참조")
    report_type: ReportType = Field(description="보고서 유형")
    report_date: date = Field(description="보고일")
    presentation_currency: str = Field(default="KRW", description="보고 통화")
    line_items: list[ReportLineItem] = Field(default_factory=list, description="보고서 라인 항목")
    entity_breakdown: list[EntityBreakdown] = Field(default_factory=list, description="법인별 내역")
    elimination_breakdown: list[EliminationBreakdown] = Field(
        default_factory=list, description="소거 내역"
    )
    nci_breakdown: NCIBreakdown | None = Field(default=None, description="비지배지분 내역")
    totals: ReportTotals = Field(default_factory=ReportTotals, description="합계")
    status: ReportStatus = Field(default=ReportStatus.DRAFT, description="보고서 상태")
    version: int = Field(default=1, description="버전")
    generated_at: datetime | None = Field(default=None, description="생성 시각")
    generated_by: str | None = Field(default=None, description="생성자")
    finalized_at: datetime | None = Field(default=None, description="확정 시각")
    finalized_by: str | None = Field(default=None, description="확정자")


class ConsolidatedReportCreate(BaseModel):
    """보고서 생성 요청 스키마."""

    period_id: str
    report_type: ReportType
    report_date: date
    presentation_currency: str = "KRW"


class ConsolidatedReportUpdate(BaseModel):
    """보고서 수정 요청 스키마."""

    status: ReportStatus | None = None
    remarks: str | None = None
