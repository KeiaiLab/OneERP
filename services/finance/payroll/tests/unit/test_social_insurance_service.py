"""4대보험 자동 산출 서비스 단위 테스트.

테스트 시나리오:
- 기본 급여 400만원 → 각 보험료 정확한 금액 검증
- 국민연금 상한 (급여 600만원 → 상한 553만원 적용)
- 급여 0원 → 모든 보험료 0
- 커스텀 요율 적용 (InsuranceRates 직접 주입)
- 일괄 산출 검증
- total_employee + total_employer = total
- 모든 금액 >= 0
- 환경변수 기반 요율 로딩 검증
- 음수 급여 → OneERPError (400)
- 장기요양보험 = 건강보험 x long_term_care_rate
"""

from __future__ import annotations

import os
from decimal import ROUND_HALF_UP, Decimal
from unittest.mock import patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_payroll_app.services.insurance_rates import InsuranceRates, get_insurance_rates
from oneerp_payroll_app.services.social_insurance_service import (
    InsuranceBreakdown,
    SocialInsuranceService,
)

# --- 기본 요율 (2026년 기준) ---
DEFAULT_RATES = InsuranceRates()


@pytest.fixture
def service() -> SocialInsuranceService:
    """기본 요율을 사용하는 서비스 인스턴스를 반환한다."""
    return SocialInsuranceService(tenant_id="test-tenant", rates=DEFAULT_RATES)


@pytest.fixture
def custom_rates() -> InsuranceRates:
    """커스텀 요율을 반환한다."""
    return InsuranceRates(
        national_pension_rate=0.05,
        national_pension_cap=6_000_000,
        health_insurance_rate=0.04,
        long_term_care_rate=0.15,
        employment_insurance_rate=0.01,
        industrial_accident_rate=0.01,
        rates_year=2027,
    )


class TestInsuranceRates:
    """InsuranceRates 설정 테스트."""

    def test_기본_요율_값(self) -> None:
        """기본 요율이 2026년 기준에 맞는지 검증한다."""
        rates = InsuranceRates()
        assert rates.national_pension_rate == 0.045
        assert rates.national_pension_cap == 5_530_000
        assert rates.health_insurance_rate == 0.03545
        assert rates.long_term_care_rate == 0.1281
        assert rates.employment_insurance_rate == 0.009
        assert rates.industrial_accident_rate == 0.007
        assert rates.rates_year == 2026

    def test_환경변수_기반_요율_로딩(self) -> None:
        """환경변수로 요율을 오버라이드할 수 있는지 검증한다."""
        env_vars = {
            "ONEERP_INS_NATIONAL_PENSION_RATE": "0.05",
            "ONEERP_INS_NATIONAL_PENSION_CAP": "6000000",
            "ONEERP_INS_HEALTH_INSURANCE_RATE": "0.04",
            "ONEERP_INS_RATES_YEAR": "2027",
        }
        with patch.dict(os.environ, env_vars):
            rates = InsuranceRates()
            assert rates.national_pension_rate == 0.05
            assert rates.national_pension_cap == 6_000_000
            assert rates.health_insurance_rate == 0.04
            assert rates.rates_year == 2027

    def test_싱글턴_캐시(self) -> None:
        """get_insurance_rates가 캐시된 인스턴스를 반환하는지 검증한다."""
        # lru_cache 초기화
        get_insurance_rates.cache_clear()
        rates1 = get_insurance_rates()
        rates2 = get_insurance_rates()
        assert rates1 is rates2
        get_insurance_rates.cache_clear()


class TestSocialInsuranceServiceCalculate:
    """SocialInsuranceService.calculate() 테스트."""

    def test_기본급여_400만원(self, service: SocialInsuranceService) -> None:
        """400만원 기본급여에 대한 각 보험료를 검증한다."""
        result = service.calculate(4_000_000)

        # 국민연금: 4,000,000 x 4.5% = 180,000
        assert result.national_pension_employee == 180_000
        assert result.national_pension_employer == 180_000

        # 건강보험: 4,000,000 x 3.545% = 141,800
        assert result.health_insurance_employee == 141_800
        assert result.health_insurance_employer == 141_800

        # 장기요양보험: 141,800 x 12.81% = 18,162.58 → 18,163 (ROUND_HALF_UP)
        expected_ltc = (Decimal(141800) * Decimal("0.1281")).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
        assert result.long_term_care_employee == expected_ltc
        assert result.long_term_care_employer == expected_ltc

        # 고용보험: 4,000,000 x 0.9% = 36,000
        assert result.employment_insurance_employee == 36_000
        assert result.employment_insurance_employer == 36_000

        # 산재보험: 4,000,000 x 0.7% = 28,000 (employer만)
        assert result.industrial_accident_employer == 28_000

    def test_국민연금_상한_적용(self, service: SocialInsuranceService) -> None:
        """급여 600만원일 때 국민연금 상한 553만원이 적용되는지 검증한다."""
        result = service.calculate(6_000_000)

        # 국민연금: min(6,000,000, 5,530,000) x 4.5% = 5,530,000 x 0.045 = 248,850
        expected_pension = round(5_530_000 * 0.045)
        assert result.national_pension_employee == expected_pension
        assert result.national_pension_employer == expected_pension

        # 건강보험은 상한 없이 600만원 기준
        expected_health = round(6_000_000 * 0.03545)
        assert result.health_insurance_employee == expected_health

    def test_급여_0원(self, service: SocialInsuranceService) -> None:
        """급여 0원일 때 모든 보험료가 0인지 검증한다."""
        result = service.calculate(0)

        assert result.national_pension_employee == 0
        assert result.national_pension_employer == 0
        assert result.health_insurance_employee == 0
        assert result.health_insurance_employer == 0
        assert result.long_term_care_employee == 0
        assert result.long_term_care_employer == 0
        assert result.employment_insurance_employee == 0
        assert result.employment_insurance_employer == 0
        assert result.industrial_accident_employer == 0
        assert result.total_employee == 0
        assert result.total_employer == 0
        assert result.total == 0

    def test_음수_급여_예외(self, service: SocialInsuranceService) -> None:
        """음수 급여 입력 시 OneERPError(400)가 발생하는지 검증한다."""
        with pytest.raises(OneERPError) as exc_info:
            service.calculate(-100_000)
        assert exc_info.value.status_code == 400
        assert "기준급여는 0 이상이어야 합니다" in str(exc_info.value.detail)

    def test_합계_일관성(self, service: SocialInsuranceService) -> None:
        """total_employee + total_employer = total 검증."""
        result = service.calculate(4_000_000)

        assert result.total == result.total_employee + result.total_employer

    def test_사용자_부담_합계(self, service: SocialInsuranceService) -> None:
        """total_employee가 사용자 부담 4개 항목 합계인지 검증한다."""
        result = service.calculate(4_000_000)

        expected = (
            result.national_pension_employee
            + result.health_insurance_employee
            + result.long_term_care_employee
            + result.employment_insurance_employee
        )
        assert result.total_employee == expected

    def test_사업주_부담_합계(self, service: SocialInsuranceService) -> None:
        """total_employer가 사업주 부담 5개 항목 합계인지 검증한다."""
        result = service.calculate(4_000_000)

        expected = (
            result.national_pension_employer
            + result.health_insurance_employer
            + result.long_term_care_employer
            + result.employment_insurance_employer
            + result.industrial_accident_employer
        )
        assert result.total_employer == expected

    def test_모든_금액_비음수(self, service: SocialInsuranceService) -> None:
        """모든 산출 금액이 0 이상인지 검증한다."""
        for salary in [0, 1_000_000, 3_000_000, 5_530_000, 10_000_000]:
            result = service.calculate(salary)
            assert result.national_pension_employee >= 0
            assert result.national_pension_employer >= 0
            assert result.health_insurance_employee >= 0
            assert result.health_insurance_employer >= 0
            assert result.long_term_care_employee >= 0
            assert result.long_term_care_employer >= 0
            assert result.employment_insurance_employee >= 0
            assert result.employment_insurance_employer >= 0
            assert result.industrial_accident_employer >= 0
            assert result.total_employee >= 0
            assert result.total_employer >= 0
            assert result.total >= 0

    def test_커스텀_요율_적용(self, custom_rates: InsuranceRates) -> None:
        """직접 주입한 커스텀 요율이 적용되는지 검증한다."""
        svc = SocialInsuranceService(tenant_id="custom-tenant", rates=custom_rates)
        result = svc.calculate(4_000_000)

        # 국민연금: 4,000,000 x 5% = 200,000
        assert result.national_pension_employee == 200_000

        # 건강보험: 4,000,000 x 4% = 160,000
        assert result.health_insurance_employee == 160_000

        # 장기요양보험: 160,000 x 15% = 24,000
        assert result.long_term_care_employee == 24_000

        # 고용보험: 4,000,000 x 1% = 40,000
        assert result.employment_insurance_employee == 40_000

        # 산재보험: 4,000,000 x 1% = 40,000
        assert result.industrial_accident_employer == 40_000

    def test_커스텀_요율_국민연금_상한(self, custom_rates: InsuranceRates) -> None:
        """커스텀 상한이 적용되는지 검증한다."""
        svc = SocialInsuranceService(tenant_id="custom-tenant", rates=custom_rates)
        result = svc.calculate(7_000_000)

        # 국민연금: min(7,000,000, 6,000,000) x 5% = 300,000
        assert result.national_pension_employee == 300_000

    def test_장기요양보험_건강보험_연동(self, service: SocialInsuranceService) -> None:
        """장기요양보험이 건강보험 x long_term_care_rate 인지 검증한다."""
        result = service.calculate(5_000_000)

        expected_long_term = (result.health_insurance_employee * Decimal("0.1281")).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
        assert result.long_term_care_employee == expected_long_term
        assert result.long_term_care_employer == expected_long_term

    def test_반환_타입(self, service: SocialInsuranceService) -> None:
        """반환 타입이 InsuranceBreakdown인지 검증한다."""
        result = service.calculate(3_000_000)
        assert isinstance(result, InsuranceBreakdown)


class TestSocialInsuranceServiceBatch:
    """SocialInsuranceService.calculate_batch() 테스트."""

    def test_일괄_산출(self, service: SocialInsuranceService) -> None:
        """여러 직원의 4대보험을 일괄 산출하는지 검증한다."""
        employees = [
            {"employee_id": "EMP-001", "base_salary": 3_000_000},
            {"employee_id": "EMP-002", "base_salary": 4_000_000},
            {"employee_id": "EMP-003", "base_salary": 6_000_000},
        ]
        results = service.calculate_batch(employees)

        assert len(results) == 3

        # 각 결과가 개별 계산과 동일한지 검증
        for emp, result in zip(employees, results, strict=True):
            individual = service.calculate(Decimal(str(emp["base_salary"])))
            assert result.total == individual.total
            assert result.total_employee == individual.total_employee
            assert result.total_employer == individual.total_employer

    def test_빈_리스트_일괄_산출(self, service: SocialInsuranceService) -> None:
        """빈 직원 리스트에 대해 빈 결과를 반환하는지 검증한다."""
        results = service.calculate_batch([])
        assert results == []

    def test_일괄_산출_합계_일관성(self, service: SocialInsuranceService) -> None:
        """일괄 산출 결과 각각의 합계가 일관적인지 검증한다."""
        employees = [
            {"employee_id": "EMP-001", "base_salary": 2_500_000},
            {"employee_id": "EMP-002", "base_salary": 8_000_000},
        ]
        results = service.calculate_batch(employees)

        for result in results:
            assert result.total == result.total_employee + result.total_employer
