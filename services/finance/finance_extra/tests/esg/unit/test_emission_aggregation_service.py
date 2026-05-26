"""배출량 집계/분류 서비스 단위 테스트.

BR-ESG-001: 탄소 배출량 자동 계산 (co2e_kg = activity x factor)
BR-ESG-002: Scope 분류 기준
BR-ESG-003: ESG 보고서 자동 집계
BR-ESG-005: 환경 목표 달성률
BR-ESG-006: 공급업체 ESG 종합 점수
BR-ESG-007: 미검증 배출 데이터 경고

참조 기준:
- GRI 305 (Emissions): Scope 1/2/3 배출 공시
- GHG Protocol: Scope 3 15개 카테고리
- K-ESG 가이드라인 (산업부/환경부)
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from oneerp_finance_extra_app.esg.services.emission_aggregation_service import (
    EmissionAggregationService,
    classify_scope,
    compute_supplier_risk_grade,
    compute_supplier_total_score,
)


class TestScope분류_BR_ESG_002:
    """BR-ESG-002: 카테고리 -> Scope 분류."""

    @pytest.mark.parametrize(
        ("category", "expected_scope"),
        [
            ("연료연소", "scope_1"),
            ("공정배출", "scope_1"),
            ("이동연소", "scope_1"),
            ("탈루배출", "scope_1"),
            ("전력사용", "scope_2"),
            ("열사용", "scope_2"),
            ("증기사용", "scope_2"),
            ("공급망", "scope_3"),
            ("출장", "scope_3"),
            ("통근", "scope_3"),
            ("폐기물처리", "scope_3"),
            ("운송", "scope_3"),
        ],
    )
    def test_카테고리_매핑(self, category: str, expected_scope: str) -> None:
        assert classify_scope(category) == expected_scope

    def test_알수없는_카테고리_기본_scope_3(self) -> None:
        """GHG Protocol의 보수적 기본값: 미분류는 Scope 3로."""
        assert classify_scope("알수없음") == "scope_3"


class TestCO2e_계산_BR_ESG_001:
    """BR-ESG-001: co2e_kg = activity_amount x emission_factor_value."""

    def test_디젤_10000L_2_6계수(self) -> None:
        """L2 예시: 10,000L x 2.6 = 26,000 kgCO2e."""
        service = EmissionAggregationService()
        co2e = service.calculate_co2e(
            activity_amount=Decimal(10_000),
            emission_factor=Decimal("2.6"),
        )
        assert co2e == Decimal(26_000)

    def test_전력_100000kWh_한국계수(self) -> None:
        """L2 예시: 100,000 x 0.4594 = 45,940 kgCO2e."""
        service = EmissionAggregationService()
        co2e = service.calculate_co2e(
            activity_amount=Decimal(100_000),
            emission_factor=Decimal("0.4594"),
        )
        assert co2e == Decimal(45940)

    def test_0_활동량_0(self) -> None:
        service = EmissionAggregationService()
        assert service.calculate_co2e(Decimal(0), Decimal("2.6")) == Decimal(0)


class Test보고서_집계_BR_ESG_003:
    """BR-ESG-003: ESGReport 생성 시 기간별 자동 집계."""

    def test_Scope별_합계_tCO2e(self) -> None:
        """배출 기록 리스트를 Scope 1/2/3으로 집계(tCO2e 단위)."""
        service = EmissionAggregationService()
        emissions = [
            {"category": "연료연소", "co2e_kg": Decimal(10_000)},
            {"category": "공정배출", "co2e_kg": Decimal(5_000)},
            {"category": "전력사용", "co2e_kg": Decimal(45_940)},
            {"category": "공급망", "co2e_kg": Decimal(100_000)},
            {"category": "출장", "co2e_kg": Decimal(20_000)},
        ]
        totals = service.aggregate_emissions_by_scope(emissions)

        # kg -> tCO2e 변환 (/1000)
        assert totals["total_scope1_co2e"] == Decimal("15.0")
        assert totals["total_scope2_co2e"] == Decimal("45.94")
        assert totals["total_scope3_co2e"] == Decimal("120.0")
        assert totals["total_co2e"] == Decimal("180.94")

    def test_빈_리스트_0집계(self) -> None:
        service = EmissionAggregationService()
        totals = service.aggregate_emissions_by_scope([])
        assert totals["total_scope1_co2e"] == Decimal(0)
        assert totals["total_scope2_co2e"] == Decimal(0)
        assert totals["total_scope3_co2e"] == Decimal(0)
        assert totals["total_co2e"] == Decimal(0)


class Test미검증_경고_BR_ESG_007:
    """BR-ESG-007: verified=false 건수 경고 (차단은 아님)."""

    def test_미검증_건수_집계(self) -> None:
        service = EmissionAggregationService()
        emissions = [
            {"verified": True},
            {"verified": False},
            {"verified": False},
            {"verified": True},
        ]
        warning = service.build_verification_warning(emissions)
        assert warning["unverified_count"] == 2
        assert warning["total_count"] == 4
        assert warning["has_unverified"] is True

    def test_전체_검증_경고_없음(self) -> None:
        service = EmissionAggregationService()
        emissions = [{"verified": True}, {"verified": True}]
        warning = service.build_verification_warning(emissions)
        assert warning["has_unverified"] is False
        assert warning["unverified_count"] == 0


class Test목표달성률_BR_ESG_005:
    """BR-ESG-005: 환경 목표 절대량/원단위 감축 달성률."""

    def test_L2_예시_75퍼센트(self) -> None:
        """기준 1,000 -> 목표 800, 현재 850 -> (1000-850)/(1000-800) = 75%."""
        service = EmissionAggregationService()
        rate = service.calculate_target_achievement_rate(
            base_value=Decimal(1000),
            target_value=Decimal(800),
            current_value=Decimal(850),
        )
        assert rate == Decimal(75)

    def test_목표_도달_100퍼센트(self) -> None:
        """현재=목표 -> 100% 달성."""
        service = EmissionAggregationService()
        rate = service.calculate_target_achievement_rate(
            base_value=Decimal(1000),
            target_value=Decimal(800),
            current_value=Decimal(800),
        )
        assert rate == Decimal(100)

    def test_기준_이상_0퍼센트(self) -> None:
        """현재가 기준값 이상 -> 0%."""
        service = EmissionAggregationService()
        rate = service.calculate_target_achievement_rate(
            base_value=Decimal(1000),
            target_value=Decimal(800),
            current_value=Decimal(1050),
        )
        assert rate == Decimal(0)

    def test_기준_목표_동일_0나눗셈_방어(self) -> None:
        """기준=목표일 때 0 division 방어."""
        service = EmissionAggregationService()
        rate = service.calculate_target_achievement_rate(
            base_value=Decimal(800),
            target_value=Decimal(800),
            current_value=Decimal(800),
        )
        assert rate == Decimal(100)


class Test공급업체_ESG점수_BR_ESG_006:
    """BR-ESG-006: E 0.4 + S 0.3 + G 0.3 가중 평균."""

    def test_L2_예시_72_68_80(self) -> None:
        """E=72, S=68, G=80 -> 73.2, B 등급."""
        total = compute_supplier_total_score(
            environmental=Decimal(72),
            social=Decimal(68),
            governance=Decimal(80),
        )
        assert total == Decimal("73.2")
        grade = compute_supplier_risk_grade(total)
        assert grade == "B"

    @pytest.mark.parametrize(
        ("score", "expected_grade"),
        [
            (Decimal(95), "A"),
            (Decimal(90), "A"),
            (Decimal(89), "B"),
            (Decimal(70), "B"),
            (Decimal(69), "C"),
            (Decimal(50), "C"),
            (Decimal(49), "D"),
            (Decimal(30), "D"),
            (Decimal(29), "F"),
            (Decimal(0), "F"),
        ],
    )
    def test_등급_경계값(self, score: Decimal, expected_grade: str) -> None:
        assert compute_supplier_risk_grade(score) == expected_grade

    def test_개선요구_플래그(self) -> None:
        """D/F 등급 -> improvement_required=True."""
        service = EmissionAggregationService()
        evaluation = service.evaluate_supplier(
            environmental=Decimal(30),
            social=Decimal(30),
            governance=Decimal(30),
        )
        assert evaluation["total_score"] == Decimal("30.0")
        assert evaluation["risk_grade"] == "D"
        assert evaluation["improvement_required"] is True

    def test_우량_A등급_개선불요(self) -> None:
        service = EmissionAggregationService()
        evaluation = service.evaluate_supplier(
            environmental=Decimal(95),
            social=Decimal(92),
            governance=Decimal(90),
        )
        assert evaluation["risk_grade"] == "A"
        assert evaluation["improvement_required"] is False
