"""탄소 발자국 계산 서비스 — Scope 1/2/3 배출량 집계."""

from __future__ import annotations

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def calculate_total_emissions(
    scope_1: Decimal,
    scope_2: Decimal,
    scope_3: Decimal,
) -> Decimal:
    """Scope 1/2/3 배출량의 합계를 계산한다.

    Args:
        scope_1: Scope 1 직접 배출량 (tCO2e).
        scope_2: Scope 2 간접 에너지 배출량 (tCO2e).
        scope_3: Scope 3 기타 간접 배출량 (tCO2e).

    Returns:
        총 배출량 (tCO2e).
    """
    return scope_1 + scope_2 + scope_3


def calculate_emission_intensity(
    total_emissions: Decimal,
    revenue: Decimal,
) -> Decimal:
    """매출 대비 배출 원단위를 계산한다.

    Args:
        total_emissions: 총 배출량 (tCO2e).
        revenue: 매출액.

    Returns:
        배출 원단위 (tCO2e/원). 매출이 0이면 Decimal("0") 반환.
    """
    if revenue == Decimal(0):
        return Decimal(0)
    return (total_emissions / revenue).quantize(Decimal("0.000001"))
