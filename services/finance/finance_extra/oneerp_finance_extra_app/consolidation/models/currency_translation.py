"""통화 환산(CurrencyTranslation) 문서 모델.

L2 엔티티 1.6 정의를 구현한다.
해외법인 재무제표의 보고통화 환산 결과를 관리한다.
K-IFRS 제1021호 환산 규칙을 적용한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class TranslationStatus(StrEnum):
    """환산 상태."""

    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class TranslationItem(BaseModel):
    """환산 항목."""

    account_code: str = Field(description="그룹 CoA 계정 코드")
    account_name: str = Field(description="계정과목명")
    account_category: str = Field(description="계정 분류 (asset/liability/equity/revenue/expense)")
    original_amount: Decimal = Field(default=Decimal(0), description="원통화 금액")
    applied_rate: Decimal = Field(default=Decimal(0), description="적용 환율")
    rate_type: str = Field(description="환율 유형 (closing/average/historical)")
    translated_amount: Decimal = Field(default=Decimal(0), description="환산 후 금액")
    translation_difference: Decimal | None = Field(default=None, description="환산 차이")


class HistoricalRate(BaseModel):
    """역사적 환율."""

    account_code: str = Field(description="적용 대상 계정 코드")
    rate: Decimal = Field(description="역사적 환율")
    rate_date: date = Field(description="환율 기준일")
    description: str | None = Field(default=None, description="설명")


class FCTADetail(BaseModel):
    """FCTA 산출 상세."""

    bs_translation_total: Decimal = Field(default=Decimal(0), description="BS 환산 합계")
    pl_translation_total: Decimal = Field(default=Decimal(0), description="PL 환산 합계")
    equity_translation_total: Decimal = Field(default=Decimal(0), description="자본 환산 합계")
    opening_fcta: Decimal = Field(default=Decimal(0), description="기초 FCTA 잔액")
    current_fcta: Decimal = Field(default=Decimal(0), description="당기 FCTA")
    closing_fcta: Decimal = Field(default=Decimal(0), description="기말 FCTA")


class CurrencyTranslation(BaseDocument):
    """통화 환산 문서."""

    period_id: str = Field(description="연결 기간")
    entity_id: str = Field(description="대상 법인")
    source_currency: str = Field(description="원통화 (기능통화)")
    target_currency: str = Field(default="KRW", description="보고통화")
    closing_rate: Decimal = Field(description="기말 환율")
    average_rate: Decimal = Field(description="평균 환율")
    historical_rates: list[HistoricalRate] = Field(default_factory=list, description="역사적 환율")
    bs_items: list[TranslationItem] = Field(default_factory=list, description="BS 환산 항목")
    pl_items: list[TranslationItem] = Field(default_factory=list, description="PL 환산 항목")
    fcta_amount: Decimal = Field(default=Decimal(0), description="해외사업환산손익 (FCTA)")
    fcta_calculation_detail: FCTADetail | None = Field(default=None, description="FCTA 산출 상세")
    total_original_assets: Decimal = Field(default=Decimal(0), description="원통화 총자산")
    total_translated_assets: Decimal = Field(default=Decimal(0), description="환산 후 총자산")
    total_original_liabilities: Decimal = Field(default=Decimal(0), description="원통화 총부채")
    total_translated_liabilities: Decimal = Field(default=Decimal(0), description="환산 후 총부채")
    status: TranslationStatus = Field(default=TranslationStatus.PENDING, description="환산 상태")
    error_message: str | None = Field(default=None, description="오류 메시지")


class CurrencyTranslationCreate(BaseModel):
    """통화 환산 생성 요청 스키마."""

    period_id: str
    entity_id: str
    source_currency: str
    target_currency: str = "KRW"
    closing_rate: Decimal
    average_rate: Decimal
    historical_rates: list[HistoricalRate] = []


class CurrencyTranslationUpdate(BaseModel):
    """통화 환산 수정 요청 스키마."""

    closing_rate: Decimal | None = None
    average_rate: Decimal | None = None
    historical_rates: list[HistoricalRate] | None = None
    status: TranslationStatus | None = None
    error_message: str | None = None
