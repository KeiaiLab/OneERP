"""총계정원장 조회 응답 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003
from decimal import Decimal

from pydantic import BaseModel, Field


class GeneralLedgerLine(BaseModel):
    """제출된 분개전표에서 파생된 총계정원장 라인."""

    entry_id: str = Field(description="journal_entry_id:line_idx 형식의 드릴다운 식별자")
    journal_entry_id: str = Field(description="원본 분개전표 ID")
    posting_date: date | None = Field(default=None, description="전기일자")
    account: str = Field(default="", description="계정과목")
    debit: Decimal = Field(default=Decimal(0), description="차변 금액")
    credit: Decimal = Field(default=Decimal(0), description="대변 금액")
    running_balance: Decimal = Field(default=Decimal(0), description="계정 누적 잔액")
    voucher_type: str = Field(default="", description="원천 전표 유형")
    voucher_no: str = Field(default="", description="원천 전표 번호")
    cost_center: str = Field(default="", description="원가센터")
    party_type: str = Field(default="", description="거래 상대방 유형")
    party: str = Field(default="", description="거래 상대방")
    remarks: str = Field(default="", description="적요")


class GeneralLedgerSummary(BaseModel):
    """총계정원장 조회 요약값."""

    opening_balance: Decimal = Field(default=Decimal(0), description="조회 시작 전 잔액")
    total_debit: Decimal = Field(default=Decimal(0), description="조회 기간 차변 합계")
    total_credit: Decimal = Field(default=Decimal(0), description="조회 기간 대변 합계")
    closing_balance: Decimal = Field(default=Decimal(0), description="조회 종료 시 잔액")
