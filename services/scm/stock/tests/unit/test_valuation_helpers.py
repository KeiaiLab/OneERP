"""valuation_helpers 이동평균 단위 테스트."""

from __future__ import annotations

from decimal import Decimal

from oneerp_stock_app.services.valuation_helpers import apply_issue_avg, apply_receipt_avg


class Test이동평균_입고:
    def test_초기_입고_단가_유지(self) -> None:
        new_qty, new_rate, new_value = apply_receipt_avg(
            prev_qty=Decimal(0),
            prev_rate=Decimal(0),
            prev_value=Decimal(0),
            qty=Decimal(10),
            rate=Decimal(100),
        )
        assert new_qty == Decimal(10)
        assert new_rate == Decimal(100)
        assert new_value == Decimal(1000)

    def test_기존재고에_고가_입고시_평균단가_상승(self) -> None:
        new_qty, new_rate, new_value = apply_receipt_avg(
            prev_qty=Decimal(10),
            prev_rate=Decimal(100),
            prev_value=Decimal(1000),
            qty=Decimal(10),
            rate=Decimal(120),
        )
        assert new_qty == Decimal(20)
        # (1000 + 10 * 120) / 20 = 2200 / 20 = 110
        assert new_rate == Decimal(110)
        assert new_value == Decimal(2200)


class Test이동평균_출고:
    def test_출고단가는_평균단가(self) -> None:
        new_qty, new_rate, new_value, out_rate = apply_issue_avg(
            prev_qty=Decimal(20),
            prev_value=Decimal(2200),
            qty=Decimal(5),
        )
        assert new_qty == Decimal(15)
        # 출고는 평균단가로 ⇒ valuation_rate 유지
        assert new_rate == Decimal(110)
        # 2200 - 5 * 110 = 1650
        assert new_value == Decimal(1650)
        assert out_rate == Decimal(110)
