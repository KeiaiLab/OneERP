"""탄소 발자국 서비스 테스트."""

from __future__ import annotations

from decimal import Decimal

from oneerp_finance_extra_app.esg.services.carbon_footprint_service import (
    calculate_emission_intensity,
    calculate_total_emissions,
)


def test_총배출량_계산() -> None:
    """Scope 1/2/3 배출량 합계를 확인한다."""
    result = calculate_total_emissions(Decimal(100), Decimal(200), Decimal(300))
    assert result == Decimal(600)


def test_배출원단위_계산() -> None:
    """매출 대비 배출 원단위를 계산한다."""
    result = calculate_emission_intensity(Decimal(600), Decimal(1_000_000))
    assert result == Decimal("0.000600")


def test_배출원단위_매출0() -> None:
    """매출이 0이면 0을 반환한다."""
    result = calculate_emission_intensity(Decimal(600), Decimal(0))
    assert result == Decimal(0)
