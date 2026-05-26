"""퇴직금 산정 서비스 - 한국 근로기준법 기반 퇴직금/평균임금 계산 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-021: 퇴직금 계산 (근로자퇴직급여 보장법 제8조)
  공식: 퇴직금 = 1일 평균임금 * 30일 * (계속근로일수 / 365)
- BR-HR-022: 평균임금 산정 (근로기준법 제2조 제6호)
  공식: 평균임금 = 산정사유 발생일 이전 3개월 임금총액 / 해당 기간 총일수
- BR-HR-023: 평균임금 < 통상임금인 경우 통상임금을 평균임금으로 간주 (최저기준)
- BR-HR-024: 계속근로기간 1년 미만 근로자는 퇴직금 지급 대상 제외
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 근로자퇴직급여 보장법 제4조 - 계속근로기간 1년 이상 시 퇴직금 지급
_MIN_YEARS_FOR_RETIREMENT_PAY = Decimal(1)

# 퇴직금 공식의 "30일분" 상수
_RETIREMENT_DAYS_MULTIPLIER = Decimal(30)

# 기준 연 일수
_YEARS_TO_DAYS = Decimal(365)


class RetirementPayService:
    """퇴직금 산정 비즈니스 로직.

    근로기준법/근로자퇴직급여 보장법에 따라 평균임금과 퇴직금을 계산한다.
    모든 금액 계산은 Decimal 로 수행하며 원 단위에서 반올림한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._employee_repo = Repository("employees", tenant_id=tenant_id)
        self._wage_repo = Repository("employee_wage_records", tenant_id=tenant_id)
        self._retirement_repo = Repository("employee_retirement_pays", tenant_id=tenant_id)

    def calculate_average_wage(
        self,
        employee_id: str,
        termination_date: date,
    ) -> dict[str, Any]:
        """BR-HR-022: 직원의 평균임금(1일치)을 산정한다.

        근로기준법 제2조 제6호 기준 - 산정사유 발생일(퇴직일) 이전 3개월 동안
        해당 근로자에게 지급된 임금의 총액을 그 기간의 총일수로 나눈 금액.

        Args:
            employee_id: 직원 ID
            termination_date: 산정사유 발생일(퇴직일)

        Returns:
            평균임금 산정 결과 dict (employee_id, period_start, period_end,
            period_days, total_wage, average_daily_wage)

        Raises:
            OneERPError: 임금 기록이 없거나 기간이 유효하지 않은 경우
        """
        # 3개월(약 92일) 전부터 퇴직일 전날까지의 임금 기록 조회
        # 근로기준법상 3개월은 퇴직일 직전 3개월을 의미 (calendar month 기반)
        period_end = termination_date
        # 월 단위 "3개월 전" 계산 (말일 안전 처리)
        y = period_end.year
        m = period_end.month - 3
        while m <= 0:
            m += 12
            y -= 1
        period_start = date(y, m, min(period_end.day, 28))

        # 해당 기간 내 임금 기록 조회
        wage_records = self._wage_repo.find_many(
            {
                "employee_id": employee_id,
                "payment_date": {
                    "$gte": period_start.isoformat(),
                    "$lt": period_end.isoformat(),
                },
            },
            limit=10000,
        )

        if not wage_records:
            raise_not_found(
                f"직원 '{employee_id}'의 최근 3개월 임금 기록이 없습니다",
            )

        total_wage = Decimal(0)
        for rec in wage_records:
            amount = rec.get("amount", 0)
            total_wage += Decimal(str(amount))

        period_days = (period_end - period_start).days
        if period_days <= 0:
            raise_unprocessable(
                "ERR-HR-040",
                "평균임금 산정 기간이 0일 이하입니다",
            )

        average_daily = (total_wage / Decimal(period_days)).quantize(
            Decimal(1),
            rounding=ROUND_HALF_UP,
        )

        logger.info(
            "평균임금 산정: %s (기간: %s~%s, 총임금: %s, 일평균: %s)",
            employee_id,
            period_start.isoformat(),
            period_end.isoformat(),
            total_wage,
            average_daily,
        )

        return {
            "employee_id": employee_id,
            "termination_date": termination_date.isoformat(),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "period_days": period_days,
            "total_wage": str(total_wage),
            "average_daily_wage": str(average_daily),
        }

    def calculate_retirement_pay(
        self,
        *,
        employee_id: str,
        termination_date: date,
        ordinary_daily_wage: Decimal | None = None,
    ) -> dict[str, Any]:
        """BR-HR-021: 퇴직금을 산정한다.

        공식 (근로자퇴직급여 보장법 제8조):
            퇴직금 = max(평균임금, 통상임금) * 30일 * (계속근로일수 / 365)

        Args:
            employee_id: 직원 ID
            termination_date: 퇴직일
            ordinary_daily_wage: 1일치 통상임금 (있으면 평균임금과 비교)

        Returns:
            퇴직금 산정 결과 dict (employee_id, hire_date, service_days,
            service_years, average_daily_wage, applied_daily_wage,
            retirement_pay, eligible)

        Raises:
            OneERPError: 직원이 없거나 입사일이 퇴직일보다 뒤인 경우
        """
        employee = self._employee_repo.find_by_id(employee_id)
        if not employee:
            raise_not_found(f"직원 '{employee_id}'을 찾을 수 없습니다")

        join_raw = employee.get("date_of_joining")
        if not join_raw:
            raise_unprocessable(
                "ERR-HR-041",
                "직원의 입사일(date_of_joining)이 등록되지 않았습니다",
            )

        if isinstance(join_raw, str):
            hire_date = date.fromisoformat(join_raw)
        elif isinstance(join_raw, date):
            hire_date = join_raw
        else:
            raise_unprocessable(
                "ERR-HR-041",
                "직원의 입사일(date_of_joining)이 등록되지 않았습니다",
            )
        if termination_date <= hire_date:
            raise_unprocessable(
                "ERR-HR-042",
                f"퇴직일({termination_date})이 입사일({hire_date}) 이후여야 합니다",
            )

        service_days = (termination_date - hire_date).days
        service_years = Decimal(service_days) / _YEARS_TO_DAYS

        # BR-HR-024: 계속근로기간 1년 미만 시 지급 대상 아님
        eligible = service_years >= _MIN_YEARS_FOR_RETIREMENT_PAY

        # 평균임금 산정
        avg_wage_info = self.calculate_average_wage(
            employee_id=employee_id,
            termination_date=termination_date,
        )
        avg_daily = Decimal(avg_wage_info["average_daily_wage"])

        # BR-HR-023: 평균임금 vs 통상임금 - 높은 값 적용
        if ordinary_daily_wage is not None and ordinary_daily_wage > avg_daily:
            applied_daily = ordinary_daily_wage
        else:
            applied_daily = avg_daily

        if eligible:
            # 공식: 일급에 30일분을 곱하고 계속근로일수를 365로 나누어 비례 적용한다
            retirement_pay = (
                applied_daily * _RETIREMENT_DAYS_MULTIPLIER * Decimal(service_days) / _YEARS_TO_DAYS
            ).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        else:
            retirement_pay = Decimal(0)

        logger.info(
            "퇴직금 산정: %s (근속일: %d, 일급: %s, 퇴직금: %s, 지급대상: %s)",
            employee_id,
            service_days,
            applied_daily,
            retirement_pay,
            eligible,
        )

        return {
            "employee_id": employee_id,
            "hire_date": hire_date.isoformat(),
            "termination_date": termination_date.isoformat(),
            "service_days": service_days,
            "service_years": str(
                service_years.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            ),
            "average_daily_wage": str(avg_daily),
            "ordinary_daily_wage": (
                str(ordinary_daily_wage) if ordinary_daily_wage is not None else None
            ),
            "applied_daily_wage": str(applied_daily),
            "retirement_pay": str(retirement_pay),
            "eligible": eligible,
        }

    def record_retirement_pay(
        self,
        *,
        employee_id: str,
        termination_date: date,
        ordinary_daily_wage: Decimal | None = None,
    ) -> dict[str, Any]:
        """퇴직금 산정 결과를 employee_retirement_pays 컬렉션에 기록한다.

        Returns:
            삽입된 퇴직금 기록 (calculation 결과 + recorded_at)
        """
        result = self.calculate_retirement_pay(
            employee_id=employee_id,
            termination_date=termination_date,
            ordinary_daily_wage=ordinary_daily_wage,
        )

        record = {
            **result,
            "recorded_at": datetime.now(UTC).isoformat(),
            "tenant_id": self._tenant_id,
        }
        self._retirement_repo.insert(record)
        logger.info(
            "퇴직금 기록 저장: %s (%s원)",
            employee_id,
            result["retirement_pay"],
        )
        return record
