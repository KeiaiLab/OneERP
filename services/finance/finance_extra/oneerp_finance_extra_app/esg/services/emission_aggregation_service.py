"""배출량 집계/분류/ESG 평가 서비스.

L2 비즈니스 룰 매핑:
- BR-ESG-001: 탄소 배출량 자동 계산 (co2e_kg = activity x factor)
- BR-ESG-002: Scope 분류 기준
- BR-ESG-003: ESG 보고서 자동 집계
- BR-ESG-005: 환경 목표 달성률
- BR-ESG-006: 공급업체 ESG 종합 점수
- BR-ESG-007: 미검증 배출 데이터 경고

참조 표준:
- GRI 305 (Emissions): Scope 1/2/3 공시 요건
- GHG Protocol Corporate Standard / Scope 3 Calculation Guidance
- K-ESG 가이드라인 (환경부/산업부, 2021)

설계 노트:
- Pure function 위주로 테스트 용이성 확보.
- 집계 단위 변환: 배출 기록은 kgCO2e, 보고서는 tCO2e (÷1000).
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Scope 분류 사전 (BR-ESG-002)
# --------------------------------------------------------------------------
_SCOPE_1_CATEGORIES: frozenset[str] = frozenset(
    {
        "연료연소",  # Stationary combustion
        "공정배출",  # Process emissions
        "이동연소",  # Mobile combustion
        "탈루배출",  # Fugitive emissions
        # 영문 alias
        "stationary_combustion",
        "process_emissions",
        "mobile_combustion",
        "fugitive",
    }
)

_SCOPE_2_CATEGORIES: frozenset[str] = frozenset(
    {
        "전력사용",  # Purchased electricity
        "열사용",  # Purchased heat
        "증기사용",  # Purchased steam
        "electricity",
        "heat",
        "steam",
    }
)

_SCOPE_3_CATEGORIES: frozenset[str] = frozenset(
    {
        "공급망",  # GHG Protocol Cat 1: Purchased goods and services
        "출장",  # Cat 6: Business travel
        "통근",  # Cat 7: Employee commuting
        "폐기물처리",  # Cat 5: Waste generated
        "운송",  # Cat 4/9: Transportation
        "purchased_goods",
        "business_travel",
        "employee_commuting",
        "waste",
        "transportation",
    }
)


def classify_scope(category: str) -> str:
    """BR-ESG-002: 카테고리를 Scope 1/2/3으로 분류한다.

    미분류 카테고리는 GHG Protocol의 보수적 원칙에 따라 Scope 3로
    기본 분류한다.
    """
    if category in _SCOPE_1_CATEGORIES:
        return "scope_1"
    if category in _SCOPE_2_CATEGORIES:
        return "scope_2"
    if category in _SCOPE_3_CATEGORIES:
        return "scope_3"
    return "scope_3"


# --------------------------------------------------------------------------
# 공급업체 ESG 평가 (BR-ESG-006) — 순수 함수 버전
# --------------------------------------------------------------------------
_WEIGHT_E = Decimal("0.4")
_WEIGHT_S = Decimal("0.3")
_WEIGHT_G = Decimal("0.3")


def compute_supplier_total_score(
    environmental: Decimal,
    social: Decimal,
    governance: Decimal,
) -> Decimal:
    """BR-ESG-006: E*0.4 + S*0.3 + G*0.3 가중 평균 점수."""
    total = environmental * _WEIGHT_E + social * _WEIGHT_S + governance * _WEIGHT_G
    # 소수점 1자리까지 반올림
    return total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def compute_supplier_risk_grade(total_score: Decimal) -> str:
    """BR-ESG-006: 리스크 등급 분류.

    A(90~100), B(70~89), C(50~69), D(30~49), F(<30)
    """
    if total_score >= Decimal(90):
        return "A"
    if total_score >= Decimal(70):
        return "B"
    if total_score >= Decimal(50):
        return "C"
    if total_score >= Decimal(30):
        return "D"
    return "F"


class EmissionAggregationService:
    """배출량 집계/보고 서비스."""

    # ---------------- BR-ESG-001 ----------------
    def calculate_co2e(
        self,
        activity_amount: Decimal,
        emission_factor: Decimal,
    ) -> Decimal:
        """BR-ESG-001: co2e_kg = activity x factor.

        Args:
            activity_amount: 활동 데이터(L, kWh, kg 등)
            emission_factor: 단위 활동당 배출계수(kgCO2e/단위)

        Returns:
            kgCO2e
        """
        return activity_amount * emission_factor

    # ---------------- BR-ESG-003 ----------------
    def aggregate_emissions_by_scope(
        self,
        emissions: list[dict[str, Any]],
    ) -> dict[str, Decimal]:
        """BR-ESG-003: Scope별 합계 (tCO2e 단위).

        Args:
            emissions: 배출 기록 리스트. 각 항목은 최소
                       ``category`` 또는 ``scope`` + ``co2e_kg``를 가진다.

        Returns:
            total_scope1_co2e, total_scope2_co2e, total_scope3_co2e, total_co2e
            (모두 tCO2e 단위)
        """
        scope_totals_kg: dict[str, Decimal] = {
            "scope_1": Decimal(0),
            "scope_2": Decimal(0),
            "scope_3": Decimal(0),
        }

        for rec in emissions:
            scope = rec.get("scope")
            if scope not in scope_totals_kg:
                category = rec.get("category", "")
                scope = classify_scope(category)

            co2e_kg = Decimal(str(rec.get("co2e_kg", 0)))
            scope_totals_kg[scope] += co2e_kg

        # kg -> t 변환
        def _to_tons(kg: Decimal) -> Decimal:
            if kg == Decimal(0):
                return Decimal(0)
            return (kg / Decimal(1000)).normalize()

        s1 = _to_tons(scope_totals_kg["scope_1"])
        s2 = _to_tons(scope_totals_kg["scope_2"])
        s3 = _to_tons(scope_totals_kg["scope_3"])
        total = s1 + s2 + s3

        return {
            "total_scope1_co2e": s1,
            "total_scope2_co2e": s2,
            "total_scope3_co2e": s3,
            "total_co2e": total,
        }

    # ---------------- BR-ESG-007 ----------------
    def build_verification_warning(
        self,
        emissions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """BR-ESG-007: 미검증 배출 기록 경고 생성.

        보고서 생성을 차단하지는 않으나, 사용자에게 검증되지 않은
        건수를 시각적으로 경고한다.
        """
        unverified = sum(1 for rec in emissions if not rec.get("verified", False))
        total = len(emissions)
        return {
            "unverified_count": unverified,
            "total_count": total,
            "has_unverified": unverified > 0,
        }

    # ---------------- BR-ESG-005 ----------------
    def calculate_target_achievement_rate(
        self,
        base_value: Decimal,
        target_value: Decimal,
        current_value: Decimal,
    ) -> Decimal:
        """BR-ESG-005: 감축 목표 달성률.

        공식 (절대량/원단위 공통):
            achievement_rate = (base - current) / (base - target) x 100

        Corner cases:
            - base == target: 감축 목표가 없다는 의미 -> 현재 ≤ target 이면 100, 아니면 0
            - current >= base: 감축 없음 -> 0%
            - current <= target: 목표 도달 -> 100% 상한
        """
        # 기준=목표: 감축 요구량 0
        if base_value == target_value:
            return Decimal(100) if current_value <= target_value else Decimal(0)

        # 현재값이 기준값 이상 -> 감축 없음
        if current_value >= base_value:
            return Decimal(0)

        reduction_needed = base_value - target_value
        reduction_achieved = base_value - current_value
        rate = reduction_achieved / reduction_needed * Decimal(100)

        # 상한 100 으로 제한 (목표 초과 달성 시)
        if rate > Decimal(100):
            return Decimal(100)
        return rate

    # ---------------- BR-ESG-006 ----------------
    def evaluate_supplier(
        self,
        environmental: Decimal,
        social: Decimal,
        governance: Decimal,
    ) -> dict[str, Any]:
        """공급업체 ESG 종합 평가.

        Returns:
            total_score, risk_grade, improvement_required 딕셔너리
        """
        total = compute_supplier_total_score(environmental, social, governance)
        grade = compute_supplier_risk_grade(total)
        improvement = grade in ("D", "F")

        return {
            "total_score": total,
            "risk_grade": grade,
            "improvement_required": improvement,
        }
