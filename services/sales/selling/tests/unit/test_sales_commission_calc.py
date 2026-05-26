"""BR-SELL-018: 영업사원 수수료 계산 테스트."""

from __future__ import annotations

from decimal import Decimal

from oneerp_selling_app.models.sales_commission import calculate_commission


class Test수수료계산:
    """BR-SELL-018: calculate_commission 함수 테스트."""

    def test_정상_수수료_계산(self) -> None:
        """BR-SELL-018: 매출액 x commission_rate / 100 = 수수료."""
        result = calculate_commission(Decimal(1_000_000), Decimal(5))
        assert result == Decimal(50_000)

    def test_수수료율_0_수수료_0(self) -> None:
        """BR-SELL-018: commission_rate=0이면 수수료=0."""
        result = calculate_commission(Decimal(1_000_000), Decimal(0))
        assert result == Decimal(0)

    def test_수수료율_음수_수수료_0(self) -> None:
        """BR-SELL-018: commission_rate 음수 시 수수료=0."""
        result = calculate_commission(Decimal(500_000), Decimal(-3))
        assert result == Decimal(0)

    def test_소수점_반올림(self) -> None:
        """BR-SELL-018: 원 단위 반올림 (ROUND_HALF_UP)."""
        # 333,333 x 3% = 9,999.99 → 반올림 → 10,000
        result = calculate_commission(Decimal(333_333), Decimal(3))
        assert result == Decimal(10_000)

    def test_소액_수수료(self) -> None:
        """BR-SELL-018: 소액 매출 시 수수료 정확성."""
        result = calculate_commission(Decimal(100), Decimal(10))
        assert result == Decimal(10)

    def test_대형_매출(self) -> None:
        """BR-SELL-018: 대형 매출 시 수수료 정확성."""
        result = calculate_commission(Decimal(1_000_000_000), Decimal("2.5"))
        assert result == Decimal(25_000_000)
