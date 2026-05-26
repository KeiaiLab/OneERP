"""퇴직금 계산 서비스 — BR-PAY-013.

퇴직금 = 1일평균임금 x 30 x (근속일수 / 365)
1일평균임금 = 최근 3개월 급여 총액 / 최근 3개월 총 일수(90일)
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, cast

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 1일평균임금 계산 기준: 최근 3개월(90일)
_RECENT_DAYS = Decimal(90)
# 퇴직금 계수: 30일
_RETIREMENT_DAYS = Decimal(30)
# 1년 일수
_YEAR_DAYS = Decimal(365)


def _round_won(value: Decimal) -> Decimal:
    """원 단위로 반올림한다 (소수점 이하 제거, ROUND_HALF_UP)."""
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


class RetirementPayService:
    """퇴직금 계산 서비스.

    BR-PAY-013: 퇴직금 = 1일평균임금 x 30 x (근속일수/365)
    1일평균임금 = 최근 3개월 급여 총액 / 90일
    """

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._employee_repo = Repository("employees", tenant_id=tenant_id)
        self._slip_repo = Repository("salary_slips", tenant_id=tenant_id)

    def calculate(self, employee_id: str, termination_date: date) -> dict[str, Any]:
        """퇴직금을 계산한다.

        Args:
            employee_id: 직원 ID
            termination_date: 퇴직일자

        Returns:
            퇴직금 계산 결과 딕셔너리

        Raises:
            OneERPError: 직원이 존재하지 않거나, 근속기간이 1년 미만이거나,
                        급여명세가 없는 경우
        """
        # 1) 직원 정보 조회 — 입사일(date_of_joining) 확인
        employee = self._employee_repo.find_by_id(employee_id)
        if not employee:
            raise_not_found(f"직원을 찾을 수 없습니다: {employee_id}")
        employee = cast("dict[str, Any]", employee)

        date_of_joining = employee.get("date_of_joining")
        if not date_of_joining:
            raise_bad_request("입사일(date_of_joining)이 설정되지 않았습니다")

        # date_of_joining이 문자열인 경우 date로 변환
        if isinstance(date_of_joining, str):
            date_of_joining = date.fromisoformat(date_of_joining)
        if not isinstance(date_of_joining, date):
            raise_bad_request("입사일(date_of_joining)이 유효한 날짜 형식이 아닙니다")
        date_of_joining = cast("date", date_of_joining)

        # 2) 근속일수 계산
        service_days = (termination_date - date_of_joining).days
        if service_days < _YEAR_DAYS:
            raise_bad_request("근속기간이 1년 미만이면 퇴직금을 지급하지 않습니다")

        # 3) 최근 3개월 급여명세 조회 (gross_pay 합산)
        slips = self._slip_repo.find_many(
            {"employee_id": employee_id},
            sort=[("posting_date", -1)],
            limit=3,
        )
        if not slips:
            raise_bad_request(f"최근 급여명세가 없습니다: {employee_id}")

        total_gross = Decimal(0)
        for slip in slips:
            total_gross += Decimal(str(slip.get("gross_pay", 0)))

        # 4) 1일평균임금 = 최근 3개월 급여 총액 / 90일
        daily_avg_wage = total_gross / _RECENT_DAYS

        # 5) 퇴직금 = 1일평균임금 x 30 x (근속일수 / 365)
        service_days_decimal = Decimal(service_days)
        retirement_amount = daily_avg_wage * _RETIREMENT_DAYS * (service_days_decimal / _YEAR_DAYS)
        retirement_amount = _round_won(retirement_amount)

        return {
            "employee_id": employee_id,
            "date_of_joining": date_of_joining.isoformat(),
            "termination_date": termination_date.isoformat(),
            "service_days": service_days,
            "total_gross_3months": _round_won(total_gross),
            "daily_avg_wage": _round_won(daily_avg_wage),
            "retirement_amount": retirement_amount,
        }
