"""연말정산 계산 서비스 단위 테스트.

테스트 시나리오:
- 근로소득공제 각 구간 (500만, 1000만, 3000만, 6000만, 1.5억)
- 누진세율 각 구간 (1000만, 3000만, 6000만, 1억, 4억)
- 근로소득 세액공제 (100만 산출세액, 200만 산출세액)
- 전체 계산 흐름 (총급여 → 최종 정산금액)
- 소득 0원 → 정산 0원
- 환급 케이스 (기납부 > 결정세액)
- 추가납부 케이스 (기납부 < 결정세액)
"""

from __future__ import annotations

import pytest
from oneerp_payroll_app.services.year_end_settlement_service import (
    YearEndSettlementResult,
    YearEndSettlementService,
)


@pytest.fixture
def service() -> YearEndSettlementService:
    """기본 서비스 인스턴스를 반환한다."""
    return YearEndSettlementService(tenant_id="test-tenant")


# ---------------------------------------------------------------------------
# 근로소득공제 테스트
# ---------------------------------------------------------------------------


class TestEarnedIncomeDeduction:
    """근로소득공제 단계별 구간 테스트."""

    def test_500만원_이하_구간(self, service: YearEndSettlementService) -> None:
        """500만원 이하: 70% 공제."""
        result = service.calculate_earned_income_deduction(5_000_000)
        # 5,000,000 x 70% = 3,500,000
        assert result == 3_500_000

    def test_1000만원_구간(self, service: YearEndSettlementService) -> None:
        """500~1500만원 구간: 350만 + 초과분의 40%."""
        result = service.calculate_earned_income_deduction(10_000_000)
        # 500만 x 70% = 350만
        # (1000만 - 500만) x 40% = 200만
        # 합계 = 550만
        assert result == 5_500_000

    def test_3000만원_구간(self, service: YearEndSettlementService) -> None:
        """1500~4500만원 구간: 750만 + 초과분의 15%."""
        result = service.calculate_earned_income_deduction(30_000_000)
        # 500만 x 70% = 350만
        # 1000만 x 40% = 400만 → 누적 750만
        # (3000만 - 1500만) x 15% = 225만
        # 합계 = 975만
        assert result == 9_750_000

    def test_6000만원_구간(self, service: YearEndSettlementService) -> None:
        """4500~1억 구간: 1200만 + 초과분의 5%."""
        result = service.calculate_earned_income_deduction(60_000_000)
        # 500만 x 70% = 350만
        # 1000만 x 40% = 400만
        # 3000만 x 15% = 450만 → 누적 1200만
        # (6000만 - 4500만) x 5% = 75만
        # 합계 = 1275만
        assert result == 12_750_000

    def test_1억5000만원_구간(self, service: YearEndSettlementService) -> None:
        """1억 초과: 1475만 + 초과분의 2%."""
        result = service.calculate_earned_income_deduction(150_000_000)
        # 500만 x 70% = 350만
        # 1000만 x 40% = 400만
        # 3000만 x 15% = 450만
        # 5500만 x 5% = 275만 → 누적 1475만
        # (1.5억 - 1억) x 2% = 100만
        # 합계 = 1575만
        assert result == 15_750_000

    def test_소득_0원(self, service: YearEndSettlementService) -> None:
        """소득 0원 → 공제 0원."""
        assert service.calculate_earned_income_deduction(0) == 0.0

    def test_음수_소득(self, service: YearEndSettlementService) -> None:
        """음수 소득 → 공제 0원."""
        assert service.calculate_earned_income_deduction(-1_000_000) == 0.0


# ---------------------------------------------------------------------------
# 누진세율 테스트
# ---------------------------------------------------------------------------


class TestTaxByBracket:
    """6단계 누진세율 테스트."""

    def test_1000만원_구간(self, service: YearEndSettlementService) -> None:
        """1400만 이하: 6%."""
        result = service.calculate_tax_by_bracket(10_000_000)
        # 1000만 x 6% = 60만
        assert result == 600_000

    def test_3000만원_구간(self, service: YearEndSettlementService) -> None:
        """1400~5000만 구간: 15%."""
        result = service.calculate_tax_by_bracket(30_000_000)
        # 1400만 x 6% = 84만
        # (3000만 - 1400만) x 15% = 240만
        # 합계 = 324만
        assert result == 3_240_000

    def test_6000만원_구간(self, service: YearEndSettlementService) -> None:
        """5000~8800만 구간: 24%."""
        result = service.calculate_tax_by_bracket(60_000_000)
        # 1400만 x 6% = 84만
        # 3600만 x 15% = 540만
        # 1000만 x 24% = 240만
        # 합계 = 864만
        assert result == 8_640_000

    def test_1억원_구간(self, service: YearEndSettlementService) -> None:
        """8800만~1.5억 구간: 35%."""
        result = service.calculate_tax_by_bracket(100_000_000)
        # 1400만 x 6% = 84만
        # 3600만 x 15% = 540만
        # 3800만 x 24% = 912만
        # 1200만 x 35% = 420만
        # 합계 = 1956만
        assert result == 19_560_000

    def test_4억원_구간(self, service: YearEndSettlementService) -> None:
        """3억~5억 구간: 40%."""
        result = service.calculate_tax_by_bracket(400_000_000)
        # 1400만 x 6% = 84만
        # 3600만 x 15% = 540만
        # 3800만 x 24% = 912만
        # 6200만 x 35% = 2170만
        # 1.5억 x 38% = 5700만
        # 1억 x 40% = 4000만 (3억~4억)
        # 합계 = 13406만
        assert result == 134_060_000

    def test_과세표준_0원(self, service: YearEndSettlementService) -> None:
        """과세표준 0원 → 세액 0원."""
        assert service.calculate_tax_by_bracket(0) == 0.0

    def test_음수_과세표준(self, service: YearEndSettlementService) -> None:
        """음수 과세표준 → 세액 0원."""
        assert service.calculate_tax_by_bracket(-5_000_000) == 0.0


# ---------------------------------------------------------------------------
# 근로소득 세액공제 테스트
# ---------------------------------------------------------------------------


class TestEarnedIncomeCredit:
    """근로소득 세액공제 테스트."""

    def test_산출세액_100만원(self, service: YearEndSettlementService) -> None:
        """산출세액 130만원 이하: 산출세액 x 55%."""
        result = service.calculate_earned_income_credit(1_000_000, total_income=40_000_000)
        # 100만 x 55% = 55만
        # 한도: 총급여 5500만 이하 → 74만
        # min(55만, 74만) = 55만
        assert result == 550_000

    def test_산출세액_200만원(self, service: YearEndSettlementService) -> None:
        """산출세액 130만원 초과: 71.5만 + (초과분 x 30%)."""
        result = service.calculate_earned_income_credit(2_000_000, total_income=40_000_000)
        # 71.5만 + (200만 - 130만) x 30% = 71.5만 + 21만 = 92.5만
        # 한도: 총급여 5500만 이하 → 74만
        # min(92.5만, 74만) = 74만
        assert result == 740_000

    def test_세액공제_한도_5500만_이하(self, service: YearEndSettlementService) -> None:
        """총급여 5500만 이하 → 한도 74만."""
        result = service.calculate_earned_income_credit(5_000_000, total_income=50_000_000)
        # 71.5만 + (500만 - 130만) x 30% = 71.5만 + 111만 = 182.5만
        # 한도 74만 적용
        assert result == 740_000

    def test_세액공제_한도_7000만_이하(self, service: YearEndSettlementService) -> None:
        """총급여 5500~7000만 → 한도 66만."""
        result = service.calculate_earned_income_credit(5_000_000, total_income=60_000_000)
        # 계산 결과 > 66만 → 한도 적용
        assert result == 660_000

    def test_세액공제_한도_1억2000만_이하(self, service: YearEndSettlementService) -> None:
        """총급여 7000~1.2억 → 한도 50만."""
        result = service.calculate_earned_income_credit(5_000_000, total_income=100_000_000)
        assert result == 500_000

    def test_세액공제_한도_1억2000만_초과(self, service: YearEndSettlementService) -> None:
        """총급여 1.2억 초과 → 한도 20만."""
        result = service.calculate_earned_income_credit(5_000_000, total_income=150_000_000)
        assert result == 200_000

    def test_산출세액_0원(self, service: YearEndSettlementService) -> None:
        """산출세액 0원 → 세액공제 0원."""
        assert service.calculate_earned_income_credit(0, total_income=50_000_000) == 0.0


# ---------------------------------------------------------------------------
# 전체 계산 흐름 테스트
# ---------------------------------------------------------------------------


class TestFullCalculation:
    """전체 연말정산 계산 흐름 테스트."""

    def test_소득_0원(self, service: YearEndSettlementService) -> None:
        """소득 0원 → 모든 항목 0, 기납부세액만큼 환급."""
        result = service.calculate(total_income=0, tax_paid=500_000)

        assert result.total_income == 0.0
        assert result.earned_income_deduction == 0.0
        assert result.taxable_income == 0.0
        assert result.calculated_tax == 0.0
        assert result.earned_income_credit == 0.0
        assert result.determined_tax == 0.0
        assert result.tax_paid == 500_000
        assert result.settlement_amount == -500_000  # 환급

    def test_환급_케이스(self, service: YearEndSettlementService) -> None:
        """기납부세액 > 결정세액 → 환급 (settlement_amount < 0)."""
        # 총급여 5000만원 → 근로소득공제 계산
        result = service.calculate(
            total_income=50_000_000,
            tax_paid=5_000_000,  # 기납부세액 500만원
        )

        assert isinstance(result, YearEndSettlementResult)
        assert result.total_income == 50_000_000
        assert result.earned_income_deduction > 0
        assert result.taxable_income > 0
        assert result.calculated_tax > 0
        assert result.settlement_amount < 0  # 환급

    def test_추가납부_케이스(self, service: YearEndSettlementService) -> None:
        """기납부세액 < 결정세액 → 추가납부 (settlement_amount > 0)."""
        result = service.calculate(
            total_income=80_000_000,
            tax_paid=1_000_000,  # 기납부세액 100만원 (너무 적게 납부)
        )

        assert result.settlement_amount > 0  # 추가납부

    def test_계산_흐름_일관성(self, service: YearEndSettlementService) -> None:
        """전체 계산 흐름의 일관성을 검증한다.

        과세표준 = 총급여 - 근로소득공제
        산출세액 = 누진세율 적용
        결정세액 = 산출세액 - 세액공제
        정산금액 = 결정세액 - 기납부세액
        """
        total_income = 60_000_000
        tax_paid = 3_000_000
        result = service.calculate(total_income=total_income, tax_paid=tax_paid)

        # 과세표준: 총급여에서 근로소득공제 차감
        expected_taxable = total_income - result.earned_income_deduction
        assert result.taxable_income == expected_taxable

        # 산출세액 = 과세표준에 누진세율 적용
        expected_tax = service.calculate_tax_by_bracket(result.taxable_income)
        assert result.calculated_tax == expected_tax

        # 근로소득 세액공제 검증
        expected_credit = service.calculate_earned_income_credit(
            result.calculated_tax, total_income
        )
        assert result.earned_income_credit == expected_credit

        # 결정세액: 산출세액에서 세액공제 차감
        expected_determined = max(result.calculated_tax - result.earned_income_credit, 0.0)
        assert result.determined_tax == expected_determined

        # 정산금액: 결정세액에서 기납부세액 차감
        expected_settlement = round(result.determined_tax - tax_paid)
        assert result.settlement_amount == expected_settlement

    def test_반환_타입(self, service: YearEndSettlementService) -> None:
        """반환 타입이 YearEndSettlementResult인지 검증한다."""
        result = service.calculate(total_income=50_000_000, tax_paid=2_000_000)
        assert isinstance(result, YearEndSettlementResult)

    def test_결정세액_비음수(self, service: YearEndSettlementService) -> None:
        """결정세액은 항상 0 이상이어야 한다 (세액공제가 산출세액 초과 시)."""
        # 소액 소득 → 산출세액이 매우 작을 수 있음
        result = service.calculate(total_income=6_000_000, tax_paid=0)
        assert result.determined_tax >= 0

    def test_고소득_케이스(self, service: YearEndSettlementService) -> None:
        """고소득자(연 2억) 계산이 정상 동작하는지 검증한다."""
        result = service.calculate(total_income=200_000_000, tax_paid=50_000_000)

        assert result.total_income == 200_000_000
        assert result.earned_income_deduction > 0
        assert result.taxable_income > 0
        assert result.calculated_tax > 0
        # 고소득자는 세액공제 한도가 작음 (20만원)
        assert result.earned_income_credit == 200_000
