"""계약 수명주기 서비스 테스트 — 인지세 계산 등."""

from __future__ import annotations

from decimal import Decimal

from oneerp_compliance_app.clm.services.contract_lifecycle_service import calculate_stamp_tax


def test_인지세_1천만원_이하_비과세() -> None:
    """1천만원 이하 계약은 인지세가 0원이다."""
    assert calculate_stamp_tax(Decimal(10_000_000)) == Decimal(0)
    assert calculate_stamp_tax(Decimal(5_000_000)) == Decimal(0)


def test_인지세_3천만원_초과() -> None:
    """3천만원 초과 ~ 5천만원 이하 계약은 인지세 2만원이다."""
    assert calculate_stamp_tax(Decimal(30_000_001)) == Decimal(20_000)


def test_인지세_5천만원_초과() -> None:
    """5천만원 초과 ~ 1억원 이하 계약은 인지세 4만원이다."""
    assert calculate_stamp_tax(Decimal(50_000_001)) == Decimal(40_000)


def test_인지세_1억원_초과() -> None:
    """1억원 초과 ~ 3억원 이하 계약은 인지세 7만원이다."""
    assert calculate_stamp_tax(Decimal(100_000_001)) == Decimal(70_000)


def test_인지세_10억원_초과() -> None:
    """10억원 초과 계약은 인지세 35만원이다."""
    assert calculate_stamp_tax(Decimal(1_000_000_001)) == Decimal(350_000)
