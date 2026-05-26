"""한국 4대보험/원천징수 세분화 계산 단위 테스트.

TDD 기반으로 각 보험료/세금 계산 메서드를 개별 검증하고,
통합 급여 계산(net_pay + employer_burden)을 검증한다.

L2 비즈니스 룰 매핑:
- BR-PAY-002: 국민연금 상한/하한 (5,900,000 / 350,000)
- BR-PAY-003: 건강보험 + 장기요양(건강보험료 x 12.95%)
- BR-PAY-004: 고용보험(근로자 0.9% / 사업주 0.9% + 고용안정 0.25%)
- BR-PAY-005: 산재보험(사업주만, 업종별 차등)
- BR-PAY-006: 소득세 원천징수 (누진세율 단순 추정)
- BR-PAY-007: 지방소득세 = 소득세 x 10%
- BR-PAY-008: 실수령액 = gross - (4대보험 + 소득세 + 지방소득세)
- BR-PAY-018: 사업주 부담 합계(employer_burden)
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import pytest
from oneerp_payroll_app.services.income_tax_service import IncomeTaxService
from oneerp_payroll_app.services.korean_insurance_service import (
    KoreanInsuranceService,
    PayrollBreakdown,
)


def _round_won(value: Decimal) -> Decimal:
    """테스트용 원 단위 반올림(ROUND_HALF_UP) — 구현과 일치."""
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


# --- KoreanInsuranceService: 국민연금 ---------------------------------------


class TestNationalPension:
    """국민연금 계산 테스트."""

    def test_일반_케이스_300만원(self) -> None:
        """월 보수 300만원 → 300만 x 4.5% = 135,000원 (십원 단위)."""
        service = KoreanInsuranceService()
        result = service.calculate_national_pension(Decimal(3000000))
        # 3,000,000 x 0.045 = 135,000 → 135,000 (십원 단위 절사)
        assert result == Decimal(135000)

    def test_상한_초과_600만원(self) -> None:
        """월 보수 600만원 → 상한 5,900,000원 적용."""
        service = KoreanInsuranceService()
        result = service.calculate_national_pension(Decimal(6000000))
        # min(6_000_000, 5_900_000) x 0.045 = 265,500 → 265,500 (십원 단위 절사)
        assert result == Decimal(265500)

    def test_하한_미달_30만원(self) -> None:
        """월 보수 30만원 → 하한 350,000원 적용."""
        service = KoreanInsuranceService()
        result = service.calculate_national_pension(Decimal(300000))
        # max(300_000, 350_000) x 0.045 = 15,750 → 15,750 (십원 단위 절사)
        assert result == Decimal(15750)

    def test_십원단위_절사(self) -> None:
        """국민연금은 십원 단위로 절사한다."""
        service = KoreanInsuranceService()
        # 1,234,567 x 0.045 = 55,555.515 → 55,550 (십원 단위 절사)
        result = service.calculate_national_pension(Decimal(1234567))
        assert result == Decimal(55550)

    def test_사업주_부담_동일(self) -> None:
        """사업주 부담도 근로자 부담과 동일 요율이다."""
        service = KoreanInsuranceService()
        employee = service.calculate_national_pension(Decimal(3000000))
        employer = service.calculate_national_pension(Decimal(3000000), is_employer=True)
        assert employee == employer


# --- KoreanInsuranceService: 건강보험 ---------------------------------------


class TestHealthInsurance:
    """건강보험 및 장기요양보험 계산 테스트."""

    def test_일반_케이스_300만원(self) -> None:
        """월 보수 300만원 → 건강 3,000,000 x 3.545% = 106,350원."""
        service = KoreanInsuranceService()
        health, ltc = service.calculate_health_insurance(Decimal(3000000))
        assert health == Decimal(106350)
        # 장기요양: 106,350 x 12.95% = 13,772.325 → 13,772
        assert ltc == Decimal(13772)

    def test_장기요양_산출_500만원(self) -> None:
        """월 보수 500만원 → 장기요양 = 건강보험료 x 12.95%."""
        service = KoreanInsuranceService()
        health, ltc = service.calculate_health_insurance(Decimal(5000000))
        # 5,000,000 x 0.03545 = 177,250
        assert health == Decimal(177250)
        # 177,250 x 0.1295 = 22,953.875 → 22,954 (원단위 반올림)
        assert ltc == Decimal(22954)

    def test_보수_0원(self) -> None:
        """월 보수 0원 → 건강/장기요양 모두 0원."""
        service = KoreanInsuranceService()
        health, ltc = service.calculate_health_insurance(Decimal(0))
        assert health == Decimal(0)
        assert ltc == Decimal(0)


# --- KoreanInsuranceService: 고용보험 ---------------------------------------


class TestEmploymentInsurance:
    """고용보험 계산 테스트."""

    def test_근로자_부담_300만원(self) -> None:
        """근로자 부담 = 월 보수 x 0.9%."""
        service = KoreanInsuranceService()
        result = service.calculate_employment_insurance(Decimal(3000000))
        # 3,000,000 x 0.009 = 27,000
        assert result == Decimal(27000)

    def test_사업주_부담_300만원(self) -> None:
        """사업주 부담 = 실업급여(0.9%) + 고용안정/직업능력개발(0.25%)."""
        service = KoreanInsuranceService()
        result = service.calculate_employment_insurance(Decimal(3000000), is_employer=True)
        # 3,000,000 x (0.009 + 0.0025) = 34,500
        assert result == Decimal(34500)

    def test_보수_0원(self) -> None:
        """보수 0원 → 고용보험 0원."""
        service = KoreanInsuranceService()
        result = service.calculate_employment_insurance(Decimal(0))
        assert result == Decimal(0)


# --- KoreanInsuranceService: 산재보험 ---------------------------------------


class TestWorkersCompensation:
    """산재보험 계산 테스트 (사업주 전액 부담)."""

    def test_디폴트_요율_1프로(self) -> None:
        """디폴트 업종 요율 1.0% → 월 보수 500만 x 1% = 50,000원."""
        service = KoreanInsuranceService()
        result = service.calculate_workers_compensation(Decimal(5000000))
        assert result == Decimal(50000)

    def test_업종_요율_변경_2프로(self) -> None:
        """업종 요율 2.0% 지정 → 월 보수 300만 x 2% = 60,000원."""
        service = KoreanInsuranceService()
        result = service.calculate_workers_compensation(
            Decimal(3000000), industry_rate=Decimal("0.02")
        )
        assert result == Decimal(60000)

    def test_업종_요율_고위험_10프로(self) -> None:
        """고위험 업종 10% → 월 보수 400만 x 10% = 400,000원."""
        service = KoreanInsuranceService()
        result = service.calculate_workers_compensation(
            Decimal(4000000), industry_rate=Decimal("0.10")
        )
        assert result == Decimal(400000)


# --- IncomeTaxService: 원천징수 단순 추정 ------------------------------------


class TestIncomeTaxWithholding:
    """소득세 원천징수(누진세율 단순 추정) 테스트."""

    def test_1인_가구_월_300만(self) -> None:
        """1인 가구, 월 300만원 급여의 원천징수 추정."""
        income_tax, local_tax = IncomeTaxService.calculate_income_tax_withholding(
            Decimal(3000000), dependents=1
        )
        # 지방소득세 = 소득세 x 10%
        assert local_tax == _round_won(income_tax * Decimal("0.1"))
        # 양수여야 한다 (월 300만은 과세 대상)
        assert income_tax > Decimal(0)

    def test_4인_가구_월_300만(self) -> None:
        """4인 가구, 월 300만원 급여 → 1인보다 세액 감소."""
        tax_1, _ = IncomeTaxService.calculate_income_tax_withholding(Decimal(3000000), dependents=1)
        tax_4, _ = IncomeTaxService.calculate_income_tax_withholding(Decimal(3000000), dependents=4)
        assert tax_4 < tax_1

    def test_고소득_월_1000만(self) -> None:
        """월 1,000만원 → 높은 세율 구간, 소득세 > 100만원."""
        income_tax, local_tax = IncomeTaxService.calculate_income_tax_withholding(
            Decimal(10000000), dependents=1
        )
        assert income_tax > Decimal(1000000)
        assert local_tax == _round_won(income_tax * Decimal("0.1"))

    def test_저소득_면세_구간(self) -> None:
        """부양가족 10인 + 월 50만 급여 → 과세표준 음수 → 소득세 0원."""
        income_tax, local_tax = IncomeTaxService.calculate_income_tax_withholding(
            Decimal(500000), dependents=10
        )
        assert income_tax == Decimal(0)
        assert local_tax == Decimal(0)

    def test_부양가족_공제_효과(self) -> None:
        """부양가족 150만원 x 인원수 만큼 과세표준이 감소한다."""
        tax_1, _ = IncomeTaxService.calculate_income_tax_withholding(Decimal(5000000), dependents=1)
        tax_3, _ = IncomeTaxService.calculate_income_tax_withholding(Decimal(5000000), dependents=3)
        # 3인 가구가 1인 가구보다 세액이 더 낮아야 한다
        assert tax_3 < tax_1


# --- KoreanInsuranceService: 통합 급여 계산 -----------------------------------


class TestCalculatePayrollIntegration:
    """통합 급여 계산 테스트 (net_pay + employer_burden)."""

    def test_월급여_300만_1인_가구(self) -> None:
        """월 300만원, 부양가족 1인 → net pay 약 260만원대 검증."""
        service = KoreanInsuranceService()
        result: PayrollBreakdown = service.calculate_payroll(
            gross_pay=Decimal(3000000),
            dependents=1,
        )

        # 총 지급액
        assert result.gross_pay == Decimal(3000000)

        # 공제 항목 존재 확인
        assert result.national_pension > Decimal(0)
        assert result.health_insurance > Decimal(0)
        assert result.long_term_care > Decimal(0)
        assert result.employment_insurance > Decimal(0)

        # 실수령액 등식 검증 (net == gross 빼기 total_deduction)
        assert result.net_pay == result.gross_pay - result.total_deduction

        # 월 300만 기준 실수령액은 대략 260만원 근처 (±5%)
        assert Decimal(2500000) < result.net_pay < Decimal(2800000)

    def test_employer_burden_별도_계산(self) -> None:
        """employer_burden이 사업주 부담(국민연금 + 건강 + 장기요양 + 고용 + 산재)으로 계산된다."""
        service = KoreanInsuranceService()
        result = service.calculate_payroll(
            gross_pay=Decimal(4000000),
            dependents=1,
            industry_rate=Decimal("0.01"),
        )
        # employer_burden 은 사업주 부담 5종 합계
        assert result.employer_burden > Decimal(0)
        # 산재보험은 사업주에만 부담 (근로자 공제에는 미포함)
        # 따라서 employer_burden > total_deduction - 소득세 - 지방소득세
        pure_insurance_employee = (
            result.national_pension
            + result.health_insurance
            + result.long_term_care
            + result.employment_insurance
        )
        assert result.employer_burden > pure_insurance_employee

    def test_net_pay_공제_합계_일치(self) -> None:
        """total_deduction = 4대보험 + 소득세 + 지방소득세 이어야 한다."""
        service = KoreanInsuranceService()
        result = service.calculate_payroll(
            gross_pay=Decimal(5000000),
            dependents=2,
        )
        expected = (
            result.national_pension
            + result.health_insurance
            + result.long_term_care
            + result.employment_insurance
            + result.income_tax
            + result.local_income_tax
        )
        assert result.total_deduction == expected

    def test_0원_급여_모두_0원(self) -> None:
        """총 지급액 0원 → 모든 공제 및 실수령액 0원."""
        service = KoreanInsuranceService()
        result = service.calculate_payroll(gross_pay=Decimal(0), dependents=1)
        assert result.gross_pay == Decimal(0)
        assert result.total_deduction == Decimal(0)
        assert result.net_pay == Decimal(0)
        assert result.employer_burden == Decimal(0)

    def test_음수_급여_예외(self) -> None:
        """음수 급여 입력 → ValueError."""
        service = KoreanInsuranceService()
        with pytest.raises(ValueError, match="0 이상"):
            service.calculate_payroll(gross_pay=Decimal(-100000), dependents=1)
