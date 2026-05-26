"""4대보험 자동 산출 서비스.

기준급여(base_salary)를 입력받아 국민연금, 건강보험, 장기요양보험,
고용보험, 산재보험을 자동으로 산출한다.

L2 비즈니스 룰 매핑:
- BR-PAY-002: 국민연금 상한 (min(base, 5,530,000) x 4.5%)
- BR-PAY-003: 건강보험 (base x 3.545%) + 장기요양 (건강 x 12.81%)
- BR-PAY-004: 고용보험 (base x 0.9%)
- BR-PAY-005: 산재보험 (base x 0.7%, 사업주만)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import cast

from oneerp_core.errors import raise_bad_request

from .insurance_rates import InsuranceRates, get_insurance_rates

logger = logging.getLogger(__name__)


@dataclass
class InsuranceBreakdown:
    """4대보험 산출 내역."""

    national_pension_employee: Decimal
    national_pension_employer: Decimal
    health_insurance_employee: Decimal
    health_insurance_employer: Decimal
    long_term_care_employee: Decimal
    long_term_care_employer: Decimal
    employment_insurance_employee: Decimal
    employment_insurance_employer: Decimal
    industrial_accident_employer: Decimal
    total_employee: Decimal  # 사용자 부담 합계
    total_employer: Decimal  # 사업주 부담 합계
    total: Decimal  # 전체 합계


def _round_won(value: Decimal) -> Decimal:
    """원 단위로 반올림한다 (소수점 이하 제거, ROUND_HALF_UP)."""
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


class SocialInsuranceService:
    """4대보험 자동 산출 서비스.

    요율은 InsuranceRates를 통해 주입받으며,
    환경변수 또는 직접 주입으로 커스터마이징 가능하다.
    """

    def __init__(self, tenant_id: str, rates: InsuranceRates | None = None) -> None:
        self.tenant_id = tenant_id
        self.rates = rates or get_insurance_rates()

    def calculate(self, base_salary: float | Decimal) -> InsuranceBreakdown:
        """기준급여 기반 4대보험을 산출한다.

        Args:
            base_salary: 기준급여 (월급)

        Returns:
            InsuranceBreakdown: 4대보험 산출 내역
        """
        salary = Decimal(str(base_salary))
        if salary < 0:
            raise_bad_request("ERR-PAY-001: 기준급여는 0 이상이어야 합니다")

        rates = self.rates

        # 1. 국민연금: 상한 적용 후 4.5% (사용자/사업주 각각)
        pension_cap = Decimal(str(rates.national_pension_cap))
        pension_base = min(salary, pension_cap)
        pension_rate = Decimal(str(rates.national_pension_rate))
        national_pension_employee = _round_won(pension_base * pension_rate)
        national_pension_employer = national_pension_employee

        # 2. 건강보험: 기준급여 x 3.545% (사용자/사업주 각각)
        health_rate = Decimal(str(rates.health_insurance_rate))
        health_insurance_employee = _round_won(salary * health_rate)
        health_insurance_employer = health_insurance_employee

        # 장기요양보험: 건강보험의 12.81% (사용자/사업주 각각)
        ltc_rate = Decimal(str(rates.long_term_care_rate))
        long_term_care_employee = _round_won(health_insurance_employee * ltc_rate)
        long_term_care_employer = long_term_care_employee

        # 3. 고용보험: 0.9% (사용자/사업주 각각)
        emp_ins_rate = Decimal(str(rates.employment_insurance_rate))
        employment_insurance_employee = _round_won(salary * emp_ins_rate)
        employment_insurance_employer = employment_insurance_employee

        # 4. 산재보험: 사업장별 차등 (기본 0.7%, employer만)
        accident_rate = Decimal(str(rates.industrial_accident_rate))
        industrial_accident_employer = _round_won(salary * accident_rate)

        # 합계 계산
        total_employee = (
            national_pension_employee
            + health_insurance_employee
            + long_term_care_employee
            + employment_insurance_employee
        )
        total_employer = (
            national_pension_employer
            + health_insurance_employer
            + long_term_care_employer
            + employment_insurance_employer
            + industrial_accident_employer
        )
        total = total_employee + total_employer

        logger.info(
            "4대보험 산출 완료: tenant=%s, base_salary=%s, total=%s",
            self.tenant_id,
            salary,
            total,
        )

        return InsuranceBreakdown(
            national_pension_employee=national_pension_employee,
            national_pension_employer=national_pension_employer,
            health_insurance_employee=health_insurance_employee,
            health_insurance_employer=health_insurance_employer,
            long_term_care_employee=long_term_care_employee,
            long_term_care_employer=long_term_care_employer,
            employment_insurance_employee=employment_insurance_employee,
            employment_insurance_employer=employment_insurance_employer,
            industrial_accident_employer=industrial_accident_employer,
            total_employee=total_employee,
            total_employer=total_employer,
            total=total,
        )

    def calculate_batch(self, employees: list[dict[str, object]]) -> list[InsuranceBreakdown]:
        """여러 직원의 4대보험을 일괄 산출한다.

        Args:
            employees: [{"employee_id": "...", "base_salary": ...}]

        Returns:
            list[InsuranceBreakdown]: 직원별 산출 내역 리스트
        """
        results: list[InsuranceBreakdown] = []
        for emp in employees:
            base_salary = Decimal(str(cast("float | int | str", emp.get("base_salary", 0))))
            breakdown = self.calculate(base_salary)
            results.append(breakdown)
        return results
