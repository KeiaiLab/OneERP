"""한국 배출권거래제(K-ETS) 서비스.

참조 규제 및 정책:
- 온실가스 배출권의 할당 및 거래에 관한 법률
- 제4차 배출권거래제 기본계획(환경부, 2026~2030)
    * 발전부문 유상할당 비율: 2026년 15% -> 2030년 50% 단계적 확대
    * 벤치마크(BM) 할당 기준 강화: 평균 -> 상위 20%
    * 사업장 단위 할당 + 무역집약도/탄소집약도 기반 유상할당 지정
- GRI 305 Emissions: Scope 1/2/3 공시 매핑

참고: ESGReport의 framework="K-ESG" 또는 "GRI" 보고 데이터 생성 시 호출된다.

설계 노트:
- 순수 함수 + 경량 Enum. Repository 의존성 없음.
- 모든 수량 단위는 tCO2e, 가격은 원/tCO2e.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

_HUNDRED = Decimal(100)


class AllocationMethod(StrEnum):
    """할당 방식."""

    GRANDFATHERING = "grandfathering"  # 과거 배출량 기반
    BENCHMARK = "benchmark"  # 제품/공정 기반 (BM)
    AUCTION = "auction"  # 유상 경매


class ComplianceStatus(StrEnum):
    """이행 상태."""

    SURPLUS = "surplus"  # 잉여 (banking 가능)
    DEFICIT = "deficit"  # 부족 (구매 필요)
    BALANCED = "balanced"  # 정확 일치


# --------------------------------------------------------------------------
# 발전부문 유상할당 비율 테이블 (제4차 기본계획)
# --------------------------------------------------------------------------
# 2026년 15%에서 시작하여 2030년 50%까지 선형 확대.
_POWER_AUCTION_START_YEAR = 2026
_POWER_AUCTION_END_YEAR = 2030
_POWER_AUCTION_START_PCT = Decimal("15.0")
_POWER_AUCTION_END_PCT = Decimal("50.0")


class KETSService:
    """K-ETS 배출권 할당/이행 로직."""

    # ------------------------------------------------------------------
    # 무상할당 — 벤치마크 기반
    # ------------------------------------------------------------------
    def calculate_benchmark_allocation(
        self,
        production_quantity: Decimal,
        benchmark_factor: Decimal,
    ) -> Decimal:
        """벤치마크 기반 무상할당 = 생산량 x BM 계수.

        Args:
            production_quantity: 생산량(제품 단위 수)
            benchmark_factor: 제품 단위당 배출계수(tCO2e/단위)

        Returns:
            무상할당량(tCO2e)
        """
        return production_quantity * benchmark_factor

    # ------------------------------------------------------------------
    # 유상할당 — 발전부문 제4차 계획기간
    # ------------------------------------------------------------------
    def get_power_sector_auction_ratio(self, year: int) -> Decimal:
        """연도별 발전부문 유상할당 비율(%) 조회.

        - 2025 이전: 0 (제4차 계획기간 이전)
        - 2026: 15% / 2030: 50% / 그 사이 선형 보간
        - 2031 이후: 50% 유지
        """
        if year < _POWER_AUCTION_START_YEAR:
            return Decimal(0)
        if year >= _POWER_AUCTION_END_YEAR:
            return _POWER_AUCTION_END_PCT

        # 선형 보간: 2026~2030 (4년 간격으로 35%p 증가)
        years_elapsed = Decimal(year - _POWER_AUCTION_START_YEAR)
        total_years = Decimal(_POWER_AUCTION_END_YEAR - _POWER_AUCTION_START_YEAR)
        delta_pct = _POWER_AUCTION_END_PCT - _POWER_AUCTION_START_PCT
        return _POWER_AUCTION_START_PCT + (delta_pct * years_elapsed / total_years)

    def calculate_power_sector_allocation(
        self,
        total_required_allowance: Decimal,
        year: int,
    ) -> dict[str, Any]:
        """발전부문 총할당 분해 — 무상할당 + 유상할당(경매 구매).

        Args:
            total_required_allowance: 총 필요 배출권(tCO2e)
            year: 할당 연도

        Returns:
            free_allocation, auction_allocation, total_allocation,
            auction_ratio_percentage
        """
        auction_pct = self.get_power_sector_auction_ratio(year)
        auction = total_required_allowance * auction_pct / _HUNDRED
        free = total_required_allowance - auction

        return {
            "free_allocation": free,
            "auction_allocation": auction,
            "total_allocation": total_required_allowance,
            "auction_ratio_percentage": auction_pct,
        }

    # ------------------------------------------------------------------
    # 이행 평가
    # ------------------------------------------------------------------
    def calculate_compliance(
        self,
        allocated: Decimal,
        actual_emissions: Decimal,
    ) -> dict[str, Any]:
        """할당량 vs 실배출량 비교.

        - allocated > actual: surplus (이월 가능)
        - allocated < actual: deficit (추가 구매 필요)
        - allocated == actual: balanced
        """
        if allocated > actual_emissions:
            return {
                "status": ComplianceStatus.SURPLUS,
                "surplus": allocated - actual_emissions,
                "deficit": Decimal(0),
            }
        if allocated < actual_emissions:
            return {
                "status": ComplianceStatus.DEFICIT,
                "surplus": Decimal(0),
                "deficit": actual_emissions - allocated,
            }
        return {
            "status": ComplianceStatus.BALANCED,
            "surplus": Decimal(0),
            "deficit": Decimal(0),
        }

    # ------------------------------------------------------------------
    # 경매 구매 비용
    # ------------------------------------------------------------------
    def calculate_auction_cost(
        self,
        quantity: Decimal,
        unit_price: Decimal,
    ) -> Decimal:
        """경매/시장 구매 비용 = 수량 x 단가.

        Args:
            quantity: 배출권 수량(tCO2e)
            unit_price: 단가(원/tCO2e)

        Returns:
            총 비용(원)
        """
        return quantity * unit_price

    # ------------------------------------------------------------------
    # 이월(Banking) 검증
    # ------------------------------------------------------------------
    def validate_banking(
        self,
        surplus: Decimal,
        requested_banking: Decimal,
        max_ratio: Decimal = Decimal("0.6"),
    ) -> dict[str, Any]:
        """이월 한도 검증 — 잉여분의 max_ratio 이내만 허용.

        Args:
            surplus: 잉여 배출권 수량
            requested_banking: 이월 요청 수량
            max_ratio: 이월 한도 비율(기본 60%, 3기 규제 기준)

        Returns:
            allowed(bool), approved_amount, excess
        """
        cap = surplus * max_ratio
        if requested_banking <= cap:
            return {
                "allowed": True,
                "approved_amount": requested_banking,
                "excess": Decimal(0),
                "cap": cap,
            }
        excess = requested_banking - cap
        return {
            "allowed": False,
            "approved_amount": cap,
            "excess": excess,
            "cap": cap,
        }

    # ------------------------------------------------------------------
    # GRI 305 매핑
    # ------------------------------------------------------------------
    def map_to_gri_305(
        self,
        scope1: Decimal,
        scope2: Decimal,
        scope3: Decimal,
    ) -> dict[str, Decimal]:
        """Scope 배출량을 GRI 305 공시 키로 매핑한다.

        GRI 305-1: Direct (Scope 1) GHG emissions
        GRI 305-2: Energy indirect (Scope 2) GHG emissions
        GRI 305-3: Other indirect (Scope 3) GHG emissions
        """
        total = scope1 + scope2 + scope3
        return {
            "GRI_305_1": scope1,
            "GRI_305_2": scope2,
            "GRI_305_3": scope3,
            "total_gross_emissions": total,
        }
