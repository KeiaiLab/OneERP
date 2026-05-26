"""한국 배출권거래제(K-ETS) 서비스 단위 테스트.

참조:
- 온실가스 배출권의 할당 및 거래에 관한 법률
- 제4차 배출권거래제 기본계획 (2026~2030)
  * 발전부문 유상할당: 2026년 15% -> 2030년 50%
  * 벤치마크(BM) 할당 기준 강화 (평균 -> 상위 20%)
  * 무역집약도/탄소집약도 기반 유상할당 대상 지정

L1/L2에서 K-ESG/K-ETS는 ESGReport 프레임워크의 일부로 다뤄진다.
본 서비스는 배출권 할당/이행/잉여분 계산을 담당한다.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from oneerp_finance_extra_app.esg.services.k_ets_service import (
    AllocationMethod,
    ComplianceStatus,
    KETSService,
)


class Test무상할당_벤치마크:
    """무상할당 — 벤치마크 기반 (BM 할당)."""

    def test_벤치마크_기반_할당_계산(self) -> None:
        """생산량 x BM 계수 = 무상할당량."""
        service = KETSService()
        allocation = service.calculate_benchmark_allocation(
            production_quantity=Decimal(1_000_000),  # 제품 단위 수
            benchmark_factor=Decimal("0.5"),  # tCO2e/단위
        )
        assert allocation == Decimal(500_000)

    def test_생산량_0_할당_0(self) -> None:
        service = KETSService()
        assert service.calculate_benchmark_allocation(
            production_quantity=Decimal(0),
            benchmark_factor=Decimal("0.5"),
        ) == Decimal(0)


class Test유상할당_발전부문:
    """유상할당 — 제4차 계획기간 발전부문 단계적 확대."""

    @pytest.mark.parametrize(
        ("year", "expected_pct"),
        [
            (2026, Decimal("15.0")),
            (2027, Decimal("23.75")),  # 선형 보간
            (2028, Decimal("32.5")),
            (2029, Decimal("41.25")),
            (2030, Decimal("50.0")),
        ],
    )
    def test_발전부문_유상할당_비율_연도별(self, year: int, expected_pct: Decimal) -> None:
        """2026년 15% -> 2030년 50% 선형 확대."""
        service = KETSService()
        pct = service.get_power_sector_auction_ratio(year)
        assert pct == expected_pct

    def test_2025년_이전_0(self) -> None:
        """제4차 계획기간 이전(~2025)은 0% 또는 기존 3기 기준."""
        service = KETSService()
        pct = service.get_power_sector_auction_ratio(2025)
        assert pct == Decimal(0)

    def test_2030년_이후_50퍼센트_유지(self) -> None:
        service = KETSService()
        pct = service.get_power_sector_auction_ratio(2031)
        assert pct == Decimal(50)


class Test총할당량_무상_유상_혼합:
    """발전부문: 총할당 = 무상 + 유상 구매."""

    def test_2026년_발전부문_할당_분해(self) -> None:
        """총 예상 100만 tCO2e, 2026년 -> 무상 85%, 유상 15%."""
        service = KETSService()
        result = service.calculate_power_sector_allocation(
            total_required_allowance=Decimal(1_000_000),
            year=2026,
        )
        assert result["free_allocation"] == Decimal(850_000)
        assert result["auction_allocation"] == Decimal(150_000)
        assert result["total_allocation"] == Decimal(1_000_000)
        assert result["auction_ratio_percentage"] == Decimal("15.0")

    def test_2030년_발전부문_할당_분해(self) -> None:
        """총 100만, 2030년 -> 무상 50%, 유상 50%."""
        service = KETSService()
        result = service.calculate_power_sector_allocation(
            total_required_allowance=Decimal(1_000_000),
            year=2030,
        )
        assert result["free_allocation"] == Decimal(500_000)
        assert result["auction_allocation"] == Decimal(500_000)


class Test이행상태_잉여부족:
    """할당량 vs 실제 배출량 비교 -> 잉여/부족 판정."""

    def test_잉여_할당_초과(self) -> None:
        """할당 100만 > 실배출 80만 -> 잉여 20만."""
        service = KETSService()
        result = service.calculate_compliance(
            allocated=Decimal(1_000_000),
            actual_emissions=Decimal(800_000),
        )
        assert result["status"] == ComplianceStatus.SURPLUS
        assert result["surplus"] == Decimal(200_000)
        assert result["deficit"] == Decimal(0)

    def test_부족_할당_미달(self) -> None:
        """할당 100만 < 실배출 120만 -> 부족 20만."""
        service = KETSService()
        result = service.calculate_compliance(
            allocated=Decimal(1_000_000),
            actual_emissions=Decimal(1_200_000),
        )
        assert result["status"] == ComplianceStatus.DEFICIT
        assert result["deficit"] == Decimal(200_000)
        assert result["surplus"] == Decimal(0)

    def test_정확일치_balanced(self) -> None:
        """할당 = 실배출 -> balanced."""
        service = KETSService()
        result = service.calculate_compliance(
            allocated=Decimal(1_000_000),
            actual_emissions=Decimal(1_000_000),
        )
        assert result["status"] == ComplianceStatus.BALANCED
        assert result["surplus"] == Decimal(0)
        assert result["deficit"] == Decimal(0)


class Test배출권_구매비용:
    """부족분 구매 비용 계산 (시장 가격 x 부족량)."""

    def test_부족분_구매비용(self) -> None:
        """부족 20만 x 단가 9,000원 = 18억."""
        service = KETSService()
        cost = service.calculate_auction_cost(
            quantity=Decimal(200_000),
            unit_price=Decimal(9_000),
        )
        assert cost == Decimal(1_800_000_000)

    def test_0수량_비용_0(self) -> None:
        service = KETSService()
        cost = service.calculate_auction_cost(
            quantity=Decimal(0),
            unit_price=Decimal(9_000),
        )
        assert cost == Decimal(0)


class Test이월_차입_규제:
    """이월(Banking) / 차입(Borrowing) 한도."""

    def test_이월한도_내(self) -> None:
        """잉여분의 60% 이내까지 이월 가능(3기 기준)."""
        service = KETSService()
        result = service.validate_banking(
            surplus=Decimal(100_000),
            requested_banking=Decimal(60_000),
            max_ratio=Decimal("0.6"),
        )
        assert result["allowed"] is True
        assert result["approved_amount"] == Decimal(60_000)

    def test_이월한도_초과(self) -> None:
        """한도 초과 요청 -> 허용 금액으로 자동 제한."""
        service = KETSService()
        result = service.validate_banking(
            surplus=Decimal(100_000),
            requested_banking=Decimal(80_000),
            max_ratio=Decimal("0.6"),
        )
        assert result["allowed"] is False
        assert result["approved_amount"] == Decimal(60_000)
        assert result["excess"] == Decimal(20_000)


class Test할당방식_Enum:
    """할당 방식 enum."""

    def test_enum_값(self) -> None:
        assert AllocationMethod.GRANDFATHERING == "grandfathering"
        assert AllocationMethod.BENCHMARK == "benchmark"
        assert AllocationMethod.AUCTION == "auction"


class TestGRI_305_매핑:
    """K-ETS 산출물을 GRI 305 공시 형식으로 매핑."""

    def test_305_1_305_2_매핑(self) -> None:
        """GRI 305-1 = Scope 1, 305-2 = Scope 2, 305-3 = Scope 3."""
        service = KETSService()
        mapped = service.map_to_gri_305(
            scope1=Decimal(1000),
            scope2=Decimal(2000),
            scope3=Decimal(3000),
        )
        assert mapped["GRI_305_1"] == Decimal(1000)
        assert mapped["GRI_305_2"] == Decimal(2000)
        assert mapped["GRI_305_3"] == Decimal(3000)

    def test_총배출량_305_1_305_2_합(self) -> None:
        """GRI 305 총 배출량 공시 = 모든 Scope 합."""
        service = KETSService()
        mapped = service.map_to_gri_305(
            scope1=Decimal(1000),
            scope2=Decimal(2000),
            scope3=Decimal(3000),
        )
        assert mapped["total_gross_emissions"] == Decimal(6000)
