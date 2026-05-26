"""재고 평가 헬퍼 — stock_ledger_service 의 이동평균 계산 중복 제거 대상.

M1-3 도입 목적:
- `stock_ledger_service.py` 의 `_process_receipt_items` / `_process_se_receipt`
  / `_process_se_issue` / `_process_se_transfer` / `_process_se_manufacture`
  5개 메서드에 각기 다른 방식으로 구현돼 있던 이동평균 로직을 `core.valuation`
  Strategy 에 **위임**하여 단일 출처화한다.
- M1-3 단계에서는 **헬퍼 함수만** 준비하고, 실제 서비스 교체는 M3 Wave A 에서.

사용 (M3 이후 예시):
    from oneerp_stock_app.services.valuation_helpers import apply_receipt_avg, apply_issue_avg

    new_bin, sle_rate = apply_receipt_avg(prev_bin, qty, rate)
    new_bin, out_rate = apply_issue_avg(prev_bin, qty)
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.valuation import MovingAverageStrategy, StockBin

# 모듈-레벨 싱글턴 — strategy 는 상태 없음
_STRATEGY = MovingAverageStrategy()


def apply_receipt_avg(
    prev_qty: Decimal,
    prev_rate: Decimal,
    prev_value: Decimal,
    qty: Decimal,
    rate: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """입고(receipt) 이동평균 적용.

    Returns:
        (new_qty, new_rate, new_value).
    """
    prev = StockBin(qty=prev_qty, valuation_rate=prev_rate, stock_value=prev_value)
    result = _STRATEGY.on_inflow(prev, qty=qty, rate=rate)
    return (
        result.new_bin.qty,
        result.new_bin.valuation_rate,
        result.new_bin.stock_value,
    )


def apply_issue_avg(
    prev_qty: Decimal,
    prev_value: Decimal,
    qty: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """출고(issue) 이동평균 적용.

    avg_rate 는 prev_value/prev_qty 로 자동 계산되므로 호출자는 별도로
    이동평균 단가를 전달하지 않아도 된다.

    Returns:
        (new_qty, new_rate, new_value, out_rate).
        out_rate 는 SLE 에 기록할 출고 단가 (= 이동평균 단가).
    """
    avg_rate = prev_value / prev_qty if prev_qty else Decimal(0)
    prev = StockBin(qty=prev_qty, valuation_rate=avg_rate, stock_value=prev_value)
    result = _STRATEGY.on_outflow(prev, qty=qty)
    return (
        result.new_bin.qty,
        result.new_bin.valuation_rate,
        result.new_bin.stock_value,
        result.out_rate,
    )
