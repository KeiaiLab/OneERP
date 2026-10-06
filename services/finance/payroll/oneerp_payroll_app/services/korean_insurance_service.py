"""한국 4대보험/원천징수 세분화 계산 서비스.

2026년 기준 한국 4대보험 요율과 간이 원천징수 누진세율을 기반으로
개별 보험료, 소득세, 지방소득세, 실수령액(net pay), 사업주 부담(employer burden)을
세분화하여 산출한다.

기존 ``SocialInsuranceService``가 전체 급여 한 건에 대한 일괄 산출을 제공하는 반면,
본 서비스는 개별 보험료별 퍼블릭 API를 제공하여 단위 테스트/UI 노출/외부 계산기 용도로
재사용하기 쉽게 설계되었다.

L2 비즈니스 룰 매핑:
- BR-PAY-002: 국민연금 상한(5,900,000) / 하한(350,000), 십원 단위 절사
- BR-PAY-003: 건강보험(3.545%) + 장기요양(건강보험료 x 12.95%)
- BR-PAY-004: 고용보험 — 근로자 0.9% / 사업주 0.9% + 고용안정/직업능력개발 0.25%
- BR-PAY-005: 산재보험 — 사업주 전액 부담, 업종 요율 디폴트 1.0%
- BR-PAY-006: 소득세 원천징수 (누진세율 단순 추정)
- BR-PAY-007: 지방소득세 = 소득세 x 10%
- BR-PAY-008: 실수령액 = 총지급액 - (4대보험 + 소득세 + 지방소득세)
- BR-PAY-018: 사업주 부담 합계(employer_burden) 별도 계산
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from oneerp_payroll_app.services.income_tax_service import IncomeTaxService

logger = logging.getLogger(__name__)

# --- 2026년 기준 요율 (사용자 지시 기준) -------------------------------------

# 국민연금: 근로자/사업주 각각 4.5%
_NATIONAL_PENSION_RATE = Decimal("0.045")
# 국민연금 보수월액 상한/하한 (2026년 기준, 사용자 지시)
_NATIONAL_PENSION_MAX = Decimal(5900000)
_NATIONAL_PENSION_MIN = Decimal(350000)

# 건강보험: 근로자/사업주 각각 3.545%
_HEALTH_INSURANCE_RATE = Decimal("0.03545")
# 장기요양보험: 건강보험료 x 12.95%
_LONG_TERM_CARE_RATE = Decimal("0.1295")

# 고용보험 — 실업급여 보험료 (근로자/사업주 동일 0.9%)
_EMPLOYMENT_INSURANCE_RATE = Decimal("0.009")
# 고용안정/직업능력개발 (사업주 추가분, 150인 미만 디폴트 0.25%)
_EMPLOYMENT_STABILITY_RATE = Decimal("0.0025")

# 산재보험 — 사업주 전액 부담, 업종별 0.7~18.6% (디폴트 1.0%)
_DEFAULT_INDUSTRY_RATE = Decimal("0.01")

# 원(KRW) 단위 정량화 기준
_ONE_WON = Decimal(1)
# 국민연금 절사 단위 — 십원
_TEN_WON = Decimal(10)


@dataclass(frozen=True)
class PayrollBreakdown:
    """통합 급여 계산 결과.

    Attributes:
        gross_pay: 총 지급액
        national_pension: 국민연금(근로자 부담)
        health_insurance: 건강보험(근로자 부담)
        long_term_care: 장기요양보험(근로자 부담)
        employment_insurance: 고용보험(근로자 부담)
        income_tax: 소득세 원천징수
        local_income_tax: 지방소득세
        total_deduction: 공제 합계
        net_pay: 실수령액 = gross_pay - total_deduction
        employer_burden: 사업주 부담 합계 (국민연금+건강+장기요양+고용+산재)
    """

    gross_pay: Decimal
    national_pension: Decimal
    health_insurance: Decimal
    long_term_care: Decimal
    employment_insurance: Decimal
    income_tax: Decimal
    local_income_tax: Decimal
    total_deduction: Decimal
    net_pay: Decimal
    employer_burden: Decimal


def _round_won(value: Decimal) -> Decimal:
    """원 단위로 반올림한다 (ROUND_HALF_UP)."""
    return value.quantize(_ONE_WON, rounding=ROUND_HALF_UP)


def _floor_ten_won(value: Decimal) -> Decimal:
    """십원 단위로 절사한다 (ROUND_DOWN).

    국민연금은 국민연금공단 고시에 따라 십원 미만을 절사한다.
    """
    return (value / _TEN_WON).quantize(_ONE_WON, rounding=ROUND_DOWN) * _TEN_WON


class KoreanInsuranceService:
    """한국 4대보험 세분화 계산 서비스.

    각 보험료별 독립 메서드를 제공하여 단위 테스트 및 재사용이 용이하게 한다.
    인스턴스 상태는 없으며 메서드는 순수 함수처럼 동작한다.
    """

    # --- 국민연금 ----------------------------------------------------------

    def calculate_national_pension(
        self,
        monthly_salary: Decimal,
        *,
        is_employer: bool = False,
    ) -> Decimal:
        """BR-PAY-002: 국민연금 계산 — 상한/하한 적용, 십원 단위 절사.

        사용자 부담과 사업주 부담 요율은 각각 4.5%로 동일하다. 본 메서드는
        ``is_employer`` 플래그와 관계없이 동일한 금액을 반환하며, 플래그는
        호출 측 가독성을 위한 마커로만 사용된다.

        Args:
            monthly_salary: 월 보수(또는 보수월액)
            is_employer: 사업주 부담 조회 여부(현재는 근로자 부담과 동일)

        Returns:
            국민연금 보험료(십원 단위 절사)

        Raises:
            ValueError: 월 보수가 음수일 때
        """
        _ = is_employer  # 마커 파라미터 (요율 동일)
        if monthly_salary < Decimal(0):
            raise ValueError("월 보수는 0 이상이어야 합니다")

        if monthly_salary == Decimal(0):
            return Decimal(0)

        # 보수월액 상/하한 적용
        base = max(_NATIONAL_PENSION_MIN, min(monthly_salary, _NATIONAL_PENSION_MAX))
        raw = base * _NATIONAL_PENSION_RATE
        return _floor_ten_won(raw)

    # --- 건강보험 + 장기요양 ----------------------------------------------

    def calculate_health_insurance(self, monthly_salary: Decimal) -> tuple[Decimal, Decimal]:
        """BR-PAY-003: 건강보험/장기요양보험 계산.

        - 건강보험 = 월 보수 x 3.545%
        - 장기요양보험 = 건강보험료 x 12.95%

        Args:
            monthly_salary: 월 보수

        Returns:
            (건강보험료, 장기요양보험료) 튜플 — 모두 원 단위 반올림

        Raises:
            ValueError: 월 보수가 음수일 때
        """
        if monthly_salary < Decimal(0):
            raise ValueError("월 보수는 0 이상이어야 합니다")

        if monthly_salary == Decimal(0):
            return Decimal(0), Decimal(0)

        health = _round_won(monthly_salary * _HEALTH_INSURANCE_RATE)
        ltc = _round_won(health * _LONG_TERM_CARE_RATE)
        return health, ltc

    # --- 고용보험 ----------------------------------------------------------

    def calculate_employment_insurance(
        self,
        monthly_salary: Decimal,
        *,
        is_employer: bool = False,
    ) -> Decimal:
        """BR-PAY-004: 고용보험 계산.

        - 근로자 부담: 월 보수 x 0.9% (실업급여)
        - 사업주 부담: 월 보수 x (0.9% + 0.25%) — 고용안정/직업능력개발 추가

        Args:
            monthly_salary: 월 보수(또는 보수총액)
            is_employer: 사업주 부담 조회 여부

        Returns:
            고용보험료

        Raises:
            ValueError: 월 보수가 음수일 때
        """
        if monthly_salary < Decimal(0):
            raise ValueError("월 보수는 0 이상이어야 합니다")

        if monthly_salary == Decimal(0):
            return Decimal(0)

        rate = _EMPLOYMENT_INSURANCE_RATE
        if is_employer:
            rate = rate + _EMPLOYMENT_STABILITY_RATE
        return _round_won(monthly_salary * rate)

    # --- 산재보험 ----------------------------------------------------------

    def calculate_workers_compensation(
        self,
        monthly_salary: Decimal,
        *,
        industry_rate: Decimal = _DEFAULT_INDUSTRY_RATE,
    ) -> Decimal:
        """BR-PAY-005: 산재보험 계산 — 사업주 전액 부담.

        Args:
            monthly_salary: 월 보수(또는 보수총액)
            industry_rate: 업종별 요율 (디폴트 1.0%)

        Returns:
            산재보험료 (사업주 부담)

        Raises:
            ValueError: 월 보수 또는 업종 요율이 음수일 때
        """
        if monthly_salary < Decimal(0):
            raise ValueError("월 보수는 0 이상이어야 합니다")
        if industry_rate < Decimal(0):
            raise ValueError("업종 요율은 0 이상이어야 합니다")

        if monthly_salary == Decimal(0):
            return Decimal(0)

        return _round_won(monthly_salary * industry_rate)

    # --- 통합 급여 계산 ----------------------------------------------------

    def calculate_payroll(
        self,
        *,
        gross_pay: Decimal,
        dependents: int = 1,
        industry_rate: Decimal = _DEFAULT_INDUSTRY_RATE,
    ) -> PayrollBreakdown:
        """BR-PAY-008 + BR-PAY-018: 통합 급여 계산 — net pay + employer burden.

        4대보험과 원천징수를 모두 호출하여 다음을 산출한다.

        1. 공제 항목
           - 국민연금(근로자)
           - 건강보험(근로자) + 장기요양(근로자)
           - 고용보험(근로자)
           - 소득세
           - 지방소득세
        2. 사업주 부담(employer_burden)
           - 국민연금(사업주)
           - 건강보험(사업주) + 장기요양(사업주)
           - 고용보험(사업주, 실업급여 + 고용안정)
           - 산재보험(사업주, 업종별 요율)
        3. net_pay = gross_pay - 공제 합계

        Args:
            gross_pay: 총 지급액 (기본급 + 수당 + 상여 등 합계)
            dependents: 부양가족 수 (본인 포함, 최소 1)
            industry_rate: 산재보험 업종 요율 (디폴트 1.0%)

        Returns:
            PayrollBreakdown: 통합 계산 결과

        Raises:
            ValueError: gross_pay가 음수일 때
        """
        if gross_pay < Decimal(0):
            raise ValueError("총 지급액은 0 이상이어야 합니다")

        if gross_pay == Decimal(0):
            return PayrollBreakdown(
                gross_pay=Decimal(0),
                national_pension=Decimal(0),
                health_insurance=Decimal(0),
                long_term_care=Decimal(0),
                employment_insurance=Decimal(0),
                income_tax=Decimal(0),
                local_income_tax=Decimal(0),
                total_deduction=Decimal(0),
                net_pay=Decimal(0),
                employer_burden=Decimal(0),
            )

        # --- 근로자 공제 항목 ----------------------------------------------
        national_pension = self.calculate_national_pension(gross_pay)
        health, ltc = self.calculate_health_insurance(gross_pay)
        employment = self.calculate_employment_insurance(gross_pay)

        income_tax, local_tax = IncomeTaxService.calculate_income_tax_withholding(
            gross_pay, dependents=dependents
        )

        total_deduction = _round_won(
            national_pension + health + ltc + employment + income_tax + local_tax
        )
        net_pay = _round_won(gross_pay - total_deduction)

        # --- 사업주 부담 ----------------------------------------------------
        employer_national_pension = self.calculate_national_pension(gross_pay, is_employer=True)
        employer_health, employer_ltc = self.calculate_health_insurance(gross_pay)
        employer_employment = self.calculate_employment_insurance(gross_pay, is_employer=True)
        workers_comp = self.calculate_workers_compensation(gross_pay, industry_rate=industry_rate)
        employer_burden = _round_won(
            employer_national_pension
            + employer_health
            + employer_ltc
            + employer_employment
            + workers_comp
        )

        logger.info(
            "통합 급여 계산 완료: gross=%s, net=%s",
            gross_pay,
            net_pay,
        )

        return PayrollBreakdown(
            gross_pay=gross_pay,
            national_pension=national_pension,
            health_insurance=health,
            long_term_care=ltc,
            employment_insurance=employment,
            income_tax=income_tax,
            local_income_tax=local_tax,
            total_deduction=total_deduction,
            net_pay=net_pay,
            employer_burden=employer_burden,
        )
