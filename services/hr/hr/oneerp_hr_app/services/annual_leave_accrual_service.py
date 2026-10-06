"""연차 유급휴가 산정 서비스 — 한국 근로기준법 제60조 정밀 구현.

L2 비즈니스 룰 매핑:
- BR-HR-030: 1년 미만 근로자 월차 (제60조 ②항)
  "1개월 개근 시 1일의 유급휴가" -> 최대 11일
- BR-HR-031: 1년 이상 근로자 연차 (제60조 ①항)
  "1년간 80% 이상 출근 시 15일의 유급휴가"
  출근률 80% 미만이면 월차 방식(근속 월수 * 1일)으로 부여
- BR-HR-032: 3년 이상 가산휴가 (제60조 ④항)
  "최초 1년을 초과하는 계속 근로연수 매 2년에 대하여 1일 가산"
  총 휴가 일수는 25일 한도
- BR-HR-033: 출근률 계산 — 출근일수 / 소정근로일수 * 100
  결근은 분모·분자 제외, 법정휴가는 출근으로 간주
- BR-HR-034: 연차 소멸 — 발생일로부터 1년간 미사용 시 소멸 (제60조 ⑦항)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.errors import raise_unprocessable

logger = logging.getLogger(__name__)

# 근로기준법 제60조 상수
_ANNUAL_BASE_DAYS = 15
_MAX_MONTHLY_ACCRUAL = 11  # 1년 미만 월차 최대 (제60조 ②항)
_MIN_ATTENDANCE_RATE_PCT = Decimal(80)  # 출근률 80%
_ADDITIONAL_START_YEAR = 3  # 가산휴가 시작 (3년 이상)
_ADDITIONAL_CYCLE_YEARS = 2  # 매 2년마다 1일 가산
_MAX_TOTAL_DAYS = 25  # 총 한도


@dataclass(frozen=True)
class AccrualResult:
    """연차 산정 결과."""

    employee_id: str
    hire_date: str
    reference_date: str
    service_years: int
    service_months: int
    attendance_rate_pct: Decimal
    base_days: int
    additional_days: int
    total_days: int
    rule_applied: str  # "under_1_year" | "annual_80_over" | "annual_80_under" | "with_additional"

    def to_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "hire_date": self.hire_date,
            "reference_date": self.reference_date,
            "service_years": self.service_years,
            "service_months": self.service_months,
            "attendance_rate_pct": str(self.attendance_rate_pct),
            "base_days": self.base_days,
            "additional_days": self.additional_days,
            "total_days": self.total_days,
            "rule_applied": self.rule_applied,
        }


class AnnualLeaveAccrualService:
    """근로기준법 제60조에 따른 연차 유급휴가 산정 전용 서비스.

    FerretDB I/O 없이 순수 계산 함수로 동작하여 단위 테스트와 배치 집계에 적합하다.
    레포지토리 연동은 기존 `LeaveService.grant_annual_leave`에서 담당한다.
    """

    def __init__(self, tenant_id: str | None = None) -> None:
        self._tenant_id = tenant_id

    # -------------------------- 근속 기간 ---------------------------
    @staticmethod
    def compute_service_duration(
        hire_date: date,
        reference_date: date,
    ) -> tuple[int, int]:
        """입사일로부터 기준일까지의 근속 (년, 월)을 계산한다.

        Args:
            hire_date: 입사일
            reference_date: 기준일 (보통 오늘 또는 회계연도 종료일)

        Returns:
            (service_years, service_months) — 만 나이 기준

        Raises:
            OneERPError: 기준일이 입사일보다 이전인 경우
        """
        if reference_date < hire_date:
            raise_unprocessable(
                "ERR-HR-060",
                f"기준일({reference_date})이 입사일({hire_date}) 이후여야 합니다",
            )

        years = reference_date.year - hire_date.year
        months = reference_date.month - hire_date.month
        if reference_date.day < hire_date.day:
            months -= 1
        while months < 0:
            years -= 1
            months += 12
        total_months = years * 12 + months
        return years, total_months

    # ------------------------- 출근률 계산 --------------------------
    @staticmethod
    def compute_attendance_rate(
        *,
        working_days: int,
        present_days: int,
    ) -> Decimal:
        """BR-HR-033: 출근률을 계산한다.

        Args:
            working_days: 소정근로일수 (법정휴일 제외한 정규 근무일 총계)
            present_days: 실제 출근일수 (법정휴가는 출근으로 간주)

        Returns:
            출근률 (0.00 ~ 100.00, 소수 둘째 자리)
        """
        if working_days < 0 or present_days < 0:
            raise_unprocessable(
                "ERR-HR-061",
                "근무일/출근일은 0 이상이어야 합니다",
            )
        if working_days == 0:
            return Decimal("0.00")
        if present_days > working_days:
            raise_unprocessable(
                "ERR-HR-062",
                f"출근일({present_days})이 근무일({working_days})보다 많습니다",
            )

        rate = (Decimal(present_days) / Decimal(working_days)) * Decimal(100)
        return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ------------------------- 연차 산정 ----------------------------
    def accrue_leave(
        self,
        *,
        employee_id: str,
        hire_date: date,
        reference_date: date,
        working_days: int,
        present_days: int,
    ) -> AccrualResult:
        """근로기준법 제60조에 따라 연차 유급휴가 일수를 산정한다.

        규칙 (BR-HR-030 ~ BR-HR-032):
          1. 근속 1년 미만 -> 근속 월수 * 1일, 최대 11일
          2. 근속 1년 이상 + 출근률 80% 이상 -> 15일
          3. 근속 1년 이상 + 출근률 80% 미만 -> 근속 월수 * 1일, 최대 11일 (제60조 ②항 준용)
          4. 근속 3년 이상 -> 기본 15일 + (근속연수 - 1) // 2 일 가산, 총 25일 한도

        Args:
            employee_id: 직원 ID
            hire_date: 입사일
            reference_date: 기준일 (회계연도 종료일 등)
            working_days: 소정근로일수
            present_days: 실제 출근일수

        Returns:
            AccrualResult — 산정 결과
        """
        years, total_months = self.compute_service_duration(hire_date, reference_date)
        rate = self.compute_attendance_rate(
            working_days=working_days,
            present_days=present_days,
        )

        if years < 1:
            # BR-HR-030: 근속 1년 미만 -> 월차 방식 (최대 11일)
            base_days = min(total_months, _MAX_MONTHLY_ACCRUAL)
            additional_days = 0
            rule = "under_1_year"
        elif rate < _MIN_ATTENDANCE_RATE_PCT:
            # BR-HR-031: 출근률 80% 미만 -> 월차 방식
            base_days = min(total_months, _MAX_MONTHLY_ACCRUAL)
            additional_days = 0
            rule = "annual_80_under"
        else:
            # BR-HR-031: 기본 15일
            base_days = _ANNUAL_BASE_DAYS

            # BR-HR-032: 3년 이상 가산휴가
            if years >= _ADDITIONAL_START_YEAR:
                # "최초 1년을 초과하는 계속 근로연수 매 2년에 대하여 1일 가산"
                additional_days = (years - 1) // _ADDITIONAL_CYCLE_YEARS
                rule = "with_additional"
            else:
                additional_days = 0
                rule = "annual_80_over"

        total = min(base_days + additional_days, _MAX_TOTAL_DAYS)
        # 가산휴가는 한도 초과분만큼만 줄어야 함 (base_days 는 그대로 유지)
        if rule == "with_additional":
            additional_days = max(0, total - base_days)

        logger.info(
            "연차 산정: 근속 %d년 %d월, 출근률 %s%%, 규칙 %s, 총 %d일",
            years,
            total_months - years * 12,
            rate,
            rule,
            total,
        )

        return AccrualResult(
            employee_id=employee_id,
            hire_date=hire_date.isoformat(),
            reference_date=reference_date.isoformat(),
            service_years=years,
            service_months=total_months,
            attendance_rate_pct=rate,
            base_days=base_days,
            additional_days=additional_days,
            total_days=total,
            rule_applied=rule,
        )

    # ----------------------- 소멸 판정 -----------------------------
    @staticmethod
    def compute_expiry_date(
        granted_at: date,
    ) -> date:
        """BR-HR-034: 연차 소멸일(발생일로부터 1년)을 계산한다.

        근로기준법 제60조 ⑦항에 따라 연차는 발생일로부터 1년간 미사용 시 소멸한다.

        Args:
            granted_at: 연차 발생일

        Returns:
            소멸일 (발생일 + 1년 - 1일)
        """
        try:
            return granted_at.replace(year=granted_at.year + 1) - timedelta(days=1)
        except ValueError:
            # 윤년 2월 29일 처리 (다음 해는 2월 28일로 보정)
            return date(granted_at.year + 1, 2, 28)
