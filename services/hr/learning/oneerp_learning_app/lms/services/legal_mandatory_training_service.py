"""한국 법정의무교육 스케줄링·이수율·미이수자 알림 서비스.

L2 사양: docs/product/scope/modules/lms/L2-spec.md

비즈니스 규칙:
- BR-LMS-009: 법정의무교육 미이수자 알림 (기한 30일/7일 전, 경과)
- BR-LMS-010: 법정의무교육 이수율 자동 계산

한국 법정 근거:
- 산업안전보건법 제29조 — 매반기 안전보건교육 (사무직 6h, 그외 12h)
- 남녀고용평등법 제13조 — 연 1회 성희롱 예방교육 (1h)
- 개인정보보호법 제28조 — 연 1회 개인정보보호 교육 (1h)
- 장애인고용촉진법 제5조의2 — 연 1회 장애인 인식개선 교육 (1h)
- 근로기준법 제93조의2 — 직장 내 괴롭힘 예방교육 (연 1회)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

logger = logging.getLogger(__name__)


class ComplianceStatus(StrEnum):
    """법정교육 이수 기한 상태."""

    ON_TRACK = "on_track"
    WARNING = "warning"  # 기한 30일 이내
    URGENT = "urgent"  # 기한 7일 이내
    OVERDUE = "overdue"  # 기한 경과


@dataclass(frozen=True)
class MandatoryTraining:
    """한국 법정의무교육 정의 (L2 ComplianceType 계열)."""

    code: str
    name: str
    law_reference: str
    frequency_per_year: int  # 연간 실시 횟수 (산안법=2, 그외=1)
    base_hours: Decimal  # 사무직 기준 시수
    production_hours: Decimal | None = None  # 생산직 시수 (산안법 전용)


# 한국 5대 법정의무교육 카탈로그 — 2026년 기준
KOREAN_MANDATORY_TRAININGS: list[MandatoryTraining] = [
    MandatoryTraining(
        code="SAFETY",
        name="산업안전보건교육",
        law_reference="산업안전보건법 제29조",
        frequency_per_year=2,  # 매반기
        base_hours=Decimal(6),  # 사무직 매반기 6h
        production_hours=Decimal(12),  # 생산직 매반기 12h
    ),
    MandatoryTraining(
        code="HARASSMENT",
        name="직장 내 성희롱 예방교육",
        law_reference="남녀고용평등법 제13조",
        frequency_per_year=1,
        base_hours=Decimal(1),
    ),
    MandatoryTraining(
        code="PRIVACY",
        name="개인정보보호 교육",
        law_reference="개인정보보호법 제28조",
        frequency_per_year=1,
        base_hours=Decimal(1),
    ),
    MandatoryTraining(
        code="DISABILITY",
        name="직장 내 장애인 인식개선 교육",
        law_reference="장애인고용촉진법 제5조의2",
        frequency_per_year=1,
        base_hours=Decimal(1),
    ),
    MandatoryTraining(
        code="WORKPLACE_BULLYING",
        name="직장 내 괴롭힘 예방교육",
        law_reference="근로기준법 제93조의2",
        frequency_per_year=1,
        base_hours=Decimal(1),
    ),
    MandatoryTraining(
        code="RETIREMENT_PENSION",
        name="퇴직연금 교육",
        law_reference="근로자퇴직급여보장법 제32조",
        frequency_per_year=1,
        base_hours=Decimal(1),
    ),
]


@dataclass(frozen=True)
class TrainingScheduleItem:
    """연간 스케줄 항목."""

    compliance_type: str
    year: int
    period_label: str
    deadline: date
    required_hours: Decimal


class LegalMandatoryTrainingService:
    """법정의무교육 서비스."""

    # ------------------------------------------------------------------
    # 카탈로그 조회
    # ------------------------------------------------------------------

    def get_training(self, compliance_type: str) -> MandatoryTraining:
        """compliance_type 코드로 카탈로그 항목을 조회한다."""
        for item in KOREAN_MANDATORY_TRAININGS:
            if item.code == compliance_type:
                return item
        msg = f"알 수 없는 법정교육 코드: {compliance_type}"
        raise ValueError(msg)

    def get_required_hours(
        self,
        *,
        compliance_type: str,
        job_category: str = "office",
    ) -> Decimal:
        """직무 카테고리별 필수 교육 시간을 반환한다.

        Args:
            compliance_type: 법정교육 코드.
            job_category: "office" (사무/판매직) 또는 "production" (생산/기타).
        """
        training = self.get_training(compliance_type)
        if training.code == "SAFETY" and job_category == "production":
            # 생산직은 매반기 12h
            return training.production_hours or training.base_hours
        return training.base_hours

    # ------------------------------------------------------------------
    # 스케줄 생성
    # ------------------------------------------------------------------

    def generate_annual_schedule(
        self,
        *,
        year: int,
        compliance_type: str,
    ) -> list[TrainingScheduleItem]:
        """연간 법정교육 스케줄을 생성한다.

        - 산업안전보건교육(매반기): 상반기 6/30, 하반기 12/31 기한 2회
        - 그 외 (연 1회): 해당 연도 12/31 기한 1회
        """
        training = self.get_training(compliance_type)
        hours = training.base_hours
        items: list[TrainingScheduleItem] = []

        if training.frequency_per_year == 2:
            items.append(
                TrainingScheduleItem(
                    compliance_type=compliance_type,
                    year=year,
                    period_label=f"{year}년 상반기",
                    deadline=date(year, 6, 30),
                    required_hours=hours,
                )
            )
            items.append(
                TrainingScheduleItem(
                    compliance_type=compliance_type,
                    year=year,
                    period_label=f"{year}년 하반기",
                    deadline=date(year, 12, 31),
                    required_hours=hours,
                )
            )
        else:
            items.append(
                TrainingScheduleItem(
                    compliance_type=compliance_type,
                    year=year,
                    period_label=f"{year}년 연간",
                    deadline=date(year, 12, 31),
                    required_hours=hours,
                )
            )
        return items

    # ------------------------------------------------------------------
    # 이수율 계산 — BR-LMS-010
    # ------------------------------------------------------------------

    def calculate_completion_rate(
        self,
        *,
        total_target: int,
        completed_count: int,
    ) -> Decimal:
        """이수율(%) = completed_count / total_target x 100.

        대상자가 0명이면 0.0 (ZeroDivision 방지).
        이수자 수가 대상자보다 많으면 ValueError.
        """
        if completed_count > total_target:
            msg = f"이수자 수({completed_count})가 대상자 수({total_target})를 초과할 수 없습니다"
            raise ValueError(msg)
        if total_target == 0:
            return Decimal("0.0")
        rate = (Decimal(completed_count) / Decimal(total_target)) * Decimal(100)
        return rate.quantize(Decimal("0.1"))

    # ------------------------------------------------------------------
    # 미이수자 알림 — BR-LMS-009
    # ------------------------------------------------------------------

    def identify_non_completers(
        self,
        *,
        target_employees: list[str],
        completed_employees: list[str],
    ) -> list[str]:
        """대상자 - 이수자를 차집합으로 계산한다 (순서 유지)."""
        completed_set = set(completed_employees)
        return [emp for emp in target_employees if emp not in completed_set]

    def evaluate_status(
        self,
        *,
        deadline: date,
        today: date,
    ) -> ComplianceStatus:
        """기한까지 남은 일수에 따른 상태를 평가한다.

        - 기한 경과 (D+1 이후): OVERDUE
        - 기한 7일 이내: URGENT
        - 기한 30일 이내: WARNING
        - 그 외: ON_TRACK
        """
        days_remaining = (deadline - today).days
        if days_remaining < 0:
            return ComplianceStatus.OVERDUE
        if days_remaining <= 7:
            return ComplianceStatus.URGENT
        if days_remaining <= 30:
            return ComplianceStatus.WARNING
        return ComplianceStatus.ON_TRACK
