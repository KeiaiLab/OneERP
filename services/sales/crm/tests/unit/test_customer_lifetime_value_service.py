"""고객 생애 가치(CLV) + 이탈 위험 서비스 단위 테스트.

BR-CRM-024: CLV 계산
BR-CRM-025: 이탈 위험 점수
BR-CRM-026: 고객 세그먼트 기반 집계
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from oneerp_crm_app.services.customer_lifetime_value_service import CustomerLifetimeValueService


@pytest.fixture
def service():
    """CustomerLifetimeValueService 인스턴스와 mock repository 생성."""
    svc = CustomerLifetimeValueService.__new__(CustomerLifetimeValueService)
    svc._tenant_id = "test-tenant"
    svc._customer_repo = MagicMock()
    svc._order_repo = MagicMock()
    svc._opp_repo = MagicMock()
    return svc


class TestCLV계산:
    """BR-CRM-024: 고객 생애 가치 계산."""

    def test_거래_없는_고객은_inactive(self, service) -> None:
        service._order_repo.find_many.return_value = []

        result = service.calculate_clv("CUST-001")

        assert result["clv"] == 0.0
        assert result["tier"] == "inactive"
        assert result["order_count"] == 0

    def test_단일_주문_CLV_계산(self, service) -> None:
        """주문 1건, 500만원, 어제 -> 소액 기본값."""
        yesterday = datetime.now(tz=UTC) - timedelta(days=1)
        service._order_repo.find_many.return_value = [
            {
                "_id": "ORD-1",
                "customer_id": "CUST-001",
                "grand_total": 5000000,
                "docstatus": 1,
                "created_at": yesterday.isoformat(),
            }
        ]

        result = service.calculate_clv("CUST-001")

        assert result["order_count"] == 1
        assert result["total_revenue"] == 5000000.0
        assert result["avg_order_value"] == 5000000.0
        assert result["clv"] > 0

    def test_복수_주문_CLV_계산(self, service) -> None:
        """3건 주문으로 평균 + 빈도 x 수명 계산."""
        base = datetime.now(tz=UTC) - timedelta(days=90)
        service._order_repo.find_many.return_value = [
            {
                "_id": f"ORD-{i}",
                "customer_id": "CUST-002",
                "grand_total": 10000000,
                "docstatus": 1,
                "created_at": (base + timedelta(days=i * 30)).isoformat(),
            }
            for i in range(3)
        ]

        result = service.calculate_clv("CUST-002")

        assert result["order_count"] == 3
        assert result["total_revenue"] == 30000000.0
        assert result["avg_order_value"] == 10000000.0
        # 약 3개월 수명, 월 1회 구매 -> CLV ≈ 1천만
        assert result["clv"] > 0
        assert result["tier"] in ("bronze", "silver", "gold", "standard")

    def test_플래티넘_등급_분류(self, service) -> None:
        """매우 큰 CLV는 platinum 등급."""
        base = datetime.now(tz=UTC) - timedelta(days=365)
        service._order_repo.find_many.return_value = [
            {
                "_id": f"ORD-{i}",
                "customer_id": "CUST-VIP",
                "grand_total": 50000000,  # 5천만원
                "docstatus": 1,
                "created_at": (base + timedelta(days=i * 30)).isoformat(),
            }
            for i in range(12)  # 월 1회, 12개월
        ]

        result = service.calculate_clv("CUST-VIP")

        # 총 6억, 평균 5천만, 월 1회, 12개월 -> CLV 6억
        assert result["total_revenue"] == 600000000.0
        assert result["tier"] == "platinum"

    def test_CLV_등급_임계값(self, service) -> None:
        """내부 분류 로직 검증."""
        from decimal import Decimal

        assert service._classify_tier(Decimal(100000001)) == "platinum"
        assert service._classify_tier(Decimal(30000000)) == "gold"
        assert service._classify_tier(Decimal(10000000)) == "silver"
        assert service._classify_tier(Decimal(1000000)) == "bronze"
        assert service._classify_tier(Decimal(500000)) == "standard"


class Test이탈위험평가:
    """BR-CRM-025: 최근 거래 갭 기반 이탈 위험."""

    def test_거래_없는_고객은_unknown(self, service) -> None:
        service._order_repo.find_many.return_value = []

        result = service.assess_churn_risk("CUST-001")

        assert result["risk_level"] == "unknown"
        assert result["risk_score"] == 0
        assert result["last_order_date"] is None

    def test_최근_10일_이내는_healthy(self, service) -> None:
        recent = datetime.now(tz=UTC) - timedelta(days=10)
        service._order_repo.find_many.return_value = [
            {
                "_id": "ORD-1",
                "grand_total": 1000000,
                "docstatus": 1,
                "created_at": recent.isoformat(),
            }
        ]

        result = service.assess_churn_risk("CUST-001")

        assert result["risk_level"] == "healthy"
        assert result["risk_score"] == 0

    def test_40일_경과는_watch(self, service) -> None:
        old = datetime.now(tz=UTC) - timedelta(days=40)
        service._order_repo.find_many.return_value = [
            {
                "_id": "ORD-1",
                "grand_total": 1000000,
                "docstatus": 1,
                "created_at": old.isoformat(),
            }
        ]

        result = service.assess_churn_risk("CUST-001")

        assert result["risk_level"] == "watch"
        assert result["risk_score"] == 25

    def test_100일_경과는_at_risk(self, service) -> None:
        old = datetime.now(tz=UTC) - timedelta(days=100)
        service._order_repo.find_many.return_value = [
            {
                "_id": "ORD-1",
                "grand_total": 1000000,
                "docstatus": 1,
                "created_at": old.isoformat(),
            }
        ]

        result = service.assess_churn_risk("CUST-001")

        assert result["risk_level"] == "at_risk"
        assert result["risk_score"] == 75

    def test_200일_경과는_churned(self, service) -> None:
        very_old = datetime.now(tz=UTC) - timedelta(days=200)
        service._order_repo.find_many.return_value = [
            {
                "_id": "ORD-1",
                "grand_total": 1000000,
                "docstatus": 1,
                "created_at": very_old.isoformat(),
            }
        ]

        result = service.assess_churn_risk("CUST-001")

        assert result["risk_level"] == "churned"
        assert result["risk_score"] == 100

    def test_복수_주문_중_가장_최근_날짜_사용(self, service) -> None:
        """여러 주문 중 가장 최근 날짜 기준."""
        dates = [
            datetime.now(tz=UTC) - timedelta(days=200),
            datetime.now(tz=UTC) - timedelta(days=50),  # 가장 최근
            datetime.now(tz=UTC) - timedelta(days=150),
        ]
        service._order_repo.find_many.return_value = [
            {
                "_id": f"ORD-{i}",
                "grand_total": 1000000,
                "docstatus": 1,
                "created_at": dt.isoformat(),
            }
            for i, dt in enumerate(dates)
        ]

        result = service.assess_churn_risk("CUST-001")

        assert result["days_since_last_order"] == 50
        assert result["risk_level"] == "watch"


class Test고객세그먼트집계:
    """BR-CRM-026: CLV/이탈 위험 고객 집계."""

    def test_at_risk_고객_목록_점수순_정렬(self, service) -> None:
        """고객 3명 중 2명이 위험 임계 이상."""
        service._customer_repo.find_many.return_value = [
            {"_id": "CUST-A"},
            {"_id": "CUST-B"},
            {"_id": "CUST-C"},
        ]

        # 고객별로 다른 주문 이력 반환
        def _order_find_many(query: dict, limit: int) -> list[dict]:
            customer_id = query.get("customer_id", "")
            if customer_id == "CUST-A":
                # 10일 전 -> healthy
                return [
                    {
                        "grand_total": 1000000,
                        "docstatus": 1,
                        "created_at": (datetime.now(tz=UTC) - timedelta(days=10)).isoformat(),
                    }
                ]
            if customer_id == "CUST-B":
                # 100일 전 -> at_risk (75)
                return [
                    {
                        "grand_total": 1000000,
                        "docstatus": 1,
                        "created_at": (datetime.now(tz=UTC) - timedelta(days=100)).isoformat(),
                    }
                ]
            if customer_id == "CUST-C":
                # 200일 전 -> churned (100)
                return [
                    {
                        "grand_total": 1000000,
                        "docstatus": 1,
                        "created_at": (datetime.now(tz=UTC) - timedelta(days=200)).isoformat(),
                    }
                ]
            return []

        service._order_repo.find_many.side_effect = _order_find_many

        at_risk = service.get_at_risk_customers(min_score=50)

        # CUST-B와 CUST-C만 포함되어야 하고, 점수 내림차순
        assert len(at_risk) == 2
        assert at_risk[0]["customer_id"] == "CUST-C"
        assert at_risk[0]["risk_score"] == 100
        assert at_risk[1]["customer_id"] == "CUST-B"
        assert at_risk[1]["risk_score"] == 75

    def test_고객_요약_미존재_시_not_found(self, service) -> None:
        """존재하지 않는 고객은 404."""
        service._customer_repo.find_by_id.return_value = None

        from oneerp_core.errors import OneERPError

        with pytest.raises(OneERPError) as exc_info:
            service.calculate_customer_summary("CUST-GHOST")
        assert exc_info.value.status_code == 404
