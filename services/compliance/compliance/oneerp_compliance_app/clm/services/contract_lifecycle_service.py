"""계약 수명주기 관리 서비스 — 인지세 계산, 만료 점검 등 비즈니스 로직."""

from __future__ import annotations

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# 한국 인지세법 기준 구간 (계약금액 → 인지세)
_STAMP_TAX_BRACKETS: list[tuple[Decimal, Decimal]] = [
    (Decimal(1_000_000_000), Decimal(350_000)),
    (Decimal(300_000_000), Decimal(150_000)),
    (Decimal(100_000_000), Decimal(70_000)),
    (Decimal(50_000_000), Decimal(40_000)),
    (Decimal(30_000_000), Decimal(20_000)),
    (Decimal(10_000_000), Decimal(0)),
]


def calculate_stamp_tax(contract_value: Decimal) -> Decimal:
    """계약 금액에 따른 한국 인지세를 계산한다.

    1천만원 이하는 비과세, 이후 구간별 정액 부과.

    Args:
        contract_value: 계약 금액.

    Returns:
        인지세 금액.
    """
    if contract_value <= Decimal(10_000_000):
        return Decimal(0)

    for threshold, tax in _STAMP_TAX_BRACKETS:
        if contract_value > threshold:
            return tax

    return Decimal(0)
