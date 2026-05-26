"""연결 기간(ConsolidationPeriod) 문서 모델.

L2 엔티티 1.4 정의를 구현한다.
연결 결산 기간의 상태 관리 및 진행 현황 추적을 담당한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class PeriodType(StrEnum):
    """기간 유형."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class PeriodStatus(StrEnum):
    """기간 상태."""

    NOT_STARTED = "not_started"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    CLOSED = "closed"
    REOPENED = "reopened"


class ProcessStatus(StrEnum):
    """처리 상태."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EntityCollectionStatus(BaseModel):
    """법인별 데이터 수집 상태."""

    entity_id: str = Field(description="CENT ID")
    entity_name: str = Field(description="법인명")
    status: str = Field(default="not_started", description="수집 상태")
    individual_period_closed: bool = Field(default=False, description="개별 회계기간 마감 여부")
    collected_at: datetime | None = Field(default=None, description="수집 완료 시각")
    validation_errors: list[str] = Field(default_factory=list, description="검증 오류 목록")
    trial_balance_total: Decimal | None = Field(
        default=None, description="잔액시산표 합계 (검증용)"
    )


class ConsolidationPeriod(BaseDocument):
    """연결 기간 문서."""

    period_name: str = Field(description="기간명")
    period_type: PeriodType = Field(default=PeriodType.MONTHLY, description="기간 유형")
    from_date: date = Field(description="시작일")
    to_date: date = Field(description="종료일")
    fiscal_year: str = Field(description="회계연도")
    status: PeriodStatus = Field(default=PeriodStatus.NOT_STARTED, description="기간 상태")
    entity_collection_status: list[EntityCollectionStatus] = Field(
        default_factory=list, description="법인별 데이터 수집 상태"
    )
    elimination_status: ProcessStatus = Field(
        default=ProcessStatus.PENDING, description="소거 처리 상태"
    )
    translation_status: ProcessStatus = Field(
        default=ProcessStatus.PENDING, description="환산 처리 상태"
    )
    consolidation_status: ProcessStatus = Field(
        default=ProcessStatus.PENDING, description="연결 합산 상태"
    )
    report_status: ProcessStatus = Field(
        default=ProcessStatus.PENDING, description="보고서 생성 상태"
    )
    opened_at: datetime | None = Field(default=None, description="개시 시각")
    opened_by: str | None = Field(default=None, description="개시자")
    closed_at: datetime | None = Field(default=None, description="마감 시각")
    closed_by: str | None = Field(default=None, description="마감자")
    total_entities: int = Field(default=0, description="연결 대상 법인 수")
    collected_entities: int = Field(default=0, description="데이터 수집 완료 법인 수")
    elimination_count: int = Field(default=0, description="소거 전표 건수")
    elimination_total_amount: Decimal = Field(default=Decimal(0), description="소거 합계 금액")
    remarks: str = Field(default="", description="비고")


class ConsolidationPeriodCreate(BaseModel):
    """연결 기간 생성 요청 스키마."""

    period_name: str
    period_type: PeriodType = PeriodType.MONTHLY
    from_date: date
    to_date: date
    fiscal_year: str
    remarks: str = ""


class ConsolidationPeriodUpdate(BaseModel):
    """연결 기간 수정 요청 스키마."""

    period_name: str | None = None
    remarks: str | None = None
