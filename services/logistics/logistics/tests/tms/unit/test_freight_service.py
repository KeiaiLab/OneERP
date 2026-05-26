"""운임 계산 서비스(FreightService) 단위 테스트.

UT-TMS-001~010, UT-TMS-019~020, UT-TMS-023 커버.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """FreightService와 mock Repository를 생성한다."""
    with patch("oneerp_logistics_app.tms.services.freight_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_logistics_app.tms.services.freight_service import FreightService

        service = FreightService(tenant_id="test-tenant")
    return service, repos


class Test운임계산:
    """BR-TMS-005/006/019: 운임 자동 계산 테스트."""

    def test_기본_화물_운임_계산(self) -> None:
        """UT-TMS-001: base + weight + fuel 계산."""
        service, repos = _make_service()
        repos["freight_rates"].find_many.return_value = [
            {
                "_id": "FR-001",
                "carrier_id": "CRR-001",
                "route_id": "RTE-001",
                "base_amount": 150000,
                "per_kg_amount": 50,
                "per_km_amount": 0,
                "fuel_surcharge_rate": 0.1,
                "weight_min_kg": 500,
                "weight_max_kg": 999999,
                "effective_from": "2026-01-01",
                "is_active": True,
            }
        ]
        repos["routes"].find_by_id.return_value = None

        result = service.calculate_freight(
            carrier_id="CRR-001",
            route_id="RTE-001",
            vehicle_type=None,
            total_weight_kg=1500,
            dispatch_date=date(2026, 3, 28),
        )

        # base=150000, weight=(1500-500)*50=50000, fuel=150000*0.1=15000
        assert result["freight_amount"] == 215000
        assert result["base_amount"] == 150000
        assert result["weight_charge"] == 50000
        assert result["fuel_surcharge"] == 15000

    def test_택배_정액_운임(self) -> None:
        """UT-TMS-002: flat rate 계산."""
        service, repos = _make_service()
        repos["freight_rates"].find_many.return_value = [
            {
                "_id": "FR-002",
                "carrier_id": "CRR-002",
                "rate_type": "flat",
                "base_amount": 4500,
                "per_kg_amount": 0,
                "per_km_amount": 0,
                "fuel_surcharge_rate": 0,
                "weight_min_kg": 0,
                "weight_max_kg": 5,
                "effective_from": "2026-01-01",
                "is_active": True,
            }
        ]

        result = service.calculate_freight(
            carrier_id="CRR-002",
            route_id=None,
            vehicle_type=None,
            total_weight_kg=3,
            dispatch_date=date(2026, 3, 28),
        )

        assert result["freight_amount"] == 4500

    def test_거리_기반_운임(self) -> None:
        """UT-TMS-003: per_km 반영."""
        service, repos = _make_service()
        repos["freight_rates"].find_many.return_value = [
            {
                "_id": "FR-003",
                "carrier_id": "CRR-003",
                "route_id": "RTE-002",
                "base_amount": 80000,
                "per_kg_amount": 30,
                "per_km_amount": 200,
                "fuel_surcharge_rate": 0.12,
                "weight_min_kg": 300,
                "weight_max_kg": 999999,
                "effective_from": "2026-01-01",
                "is_active": True,
            }
        ]
        repos["routes"].find_by_id.return_value = {"distance_km": 160}

        result = service.calculate_freight(
            carrier_id="CRR-003",
            route_id="RTE-002",
            vehicle_type=None,
            total_weight_kg=800,
            dispatch_date=date(2026, 3, 28),
        )

        # base=80000, weight=(800-300)*30=15000, distance=160*200=32000, fuel=80000*0.12=9600
        assert result["freight_amount"] == 136600

    def test_단가_미등록_시_0원(self) -> None:
        """UT-TMS-004: 운임 단가 미등록 시 0원 + 경고."""
        service, repos = _make_service()
        repos["freight_rates"].find_many.return_value = []

        result = service.calculate_freight(
            carrier_id="CRR-999",
            route_id=None,
            vehicle_type=None,
            total_weight_kg=100,
            dispatch_date=date(2026, 3, 28),
        )

        assert result["freight_amount"] == 0
        assert "warning" in result

    def test_유효기간_만료_단가_미적용(self) -> None:
        """UT-TMS-005: 만료된 단가 무시."""
        service, repos = _make_service()
        repos["freight_rates"].find_many.return_value = [
            {
                "_id": "FR-004",
                "carrier_id": "CRR-001",
                "base_amount": 100000,
                "per_kg_amount": 0,
                "per_km_amount": 0,
                "fuel_surcharge_rate": 0,
                "weight_min_kg": 0,
                "weight_max_kg": 999999,
                "effective_from": "2025-01-01",
                "effective_to": "2025-12-31",
                "is_active": True,
            }
        ]

        result = service.calculate_freight(
            carrier_id="CRR-001",
            route_id=None,
            vehicle_type=None,
            total_weight_kg=100,
            dispatch_date=date(2026, 3, 28),
        )

        assert result["freight_amount"] == 0


class Test정산금액계산:
    """BR-TMS-010/011: 정산 금액 및 세금 계산 테스트."""

    def test_기본_정산_계산(self) -> None:
        """UT-TMS-006: subtotal + fuel + tax."""
        service, _repos = _make_service()
        result = service.calculate_settlement(
            subtotal=3200000,
            fuel_surcharge=320000,
            currency="KRW",
        )

        # taxable = 3200000 + 320000 = 3520000
        # tax = FLOOR(3520000 * 0.1) = 352000
        # total = 3520000 + 352000 = 3872000
        assert result["taxable"] == 3520000
        assert result["tax_amount"] == 352000
        assert result["total_amount"] == 3872000

    def test_추가비용_차감_포함_정산(self) -> None:
        """UT-TMS-007: 추가비용/차감 반영."""
        service, _repos = _make_service()
        result = service.calculate_settlement(
            subtotal=1000000,
            fuel_surcharge=100000,
            additional_charges=[{"description": "출장비", "amount": 50000}],
            deductions=[{"description": "할인", "amount": 30000}],
            currency="KRW",
        )

        # taxable = 1000000 + 100000 + 50000 - 30000 = 1120000
        # tax = FLOOR(1120000 * 0.1) = 112000
        assert result["taxable"] == 1120000
        assert result["tax_amount"] == 112000
        assert result["total_amount"] == 1232000

    def test_원_단위_절사(self) -> None:
        """UT-TMS-008: KRW 세금 FLOOR 적용."""
        service, _repos = _make_service()
        result = service.calculate_settlement(
            subtotal=1234567,
            fuel_surcharge=0,
            currency="KRW",
        )

        # tax = FLOOR(1234567 * 0.1) = FLOOR(123456.7) = 123456
        assert result["tax_amount"] == 123456


class TestOTD계산:
    """BR-TMS-014: 정시 배송률(OTD) 테스트."""

    def test_정상_OTD(self) -> None:
        """UT-TMS-009: OTD 비율 정확 계산."""
        service, _repos = _make_service()
        shipments = [
            {"expected_delivery": "2026-03-28T14:00", "actual_delivery": "2026-03-28T13:00"},
            {"expected_delivery": "2026-03-28T14:00", "actual_delivery": "2026-03-28T15:00"},
            {"expected_delivery": "2026-03-28T14:00", "actual_delivery": "2026-03-28T14:00"},
        ]
        rate = service.calculate_otd_rate(shipments)
        # 2/3 정시 = 66.67%
        assert rate == 66.67

    def test_expected_미설정_건_제외(self) -> None:
        """UT-TMS-010: expected_delivery가 null인 건은 OTD에서 제외."""
        service, _repos = _make_service()
        shipments = [
            {"expected_delivery": "2026-03-28T14:00", "actual_delivery": "2026-03-28T13:00"},
            {"expected_delivery": None, "actual_delivery": "2026-03-28T15:00"},
        ]
        rate = service.calculate_otd_rate(shipments)
        assert rate == 100.0


class Test정시배송판정:
    """BR-TMS-014: 정시 배송 판정 테스트."""

    def test_정시배송(self) -> None:
        """UT-TMS-019: actual <= expected 시 on_time."""
        service, _repos = _make_service()
        shipments = [
            {"expected_delivery": "2026-03-28T14:00", "actual_delivery": "2026-03-28T13:30"},
        ]
        rate = service.calculate_otd_rate(shipments)
        assert rate == 100.0

    def test_지연배송(self) -> None:
        """UT-TMS-020: actual > expected 시 not on_time."""
        service, _repos = _make_service()
        shipments = [
            {"expected_delivery": "2026-03-28T14:00", "actual_delivery": "2026-03-28T15:00"},
        ]
        rate = service.calculate_otd_rate(shipments)
        assert rate == 0.0


class Test운송사성과:
    """BR-TMS-020: 운송사 성과 점수 계산 테스트."""

    def test_성과점수_계산(self) -> None:
        """UT-TMS-023: 0~5점 범위 성과 점수."""
        service, _repos = _make_service()
        score = service.calculate_carrier_performance(
            total_delivered=20,
            on_time_count=18,
            accident_count=0,
            pod_required_count=15,
            pod_submitted_count=15,
        )

        assert score is not None
        assert 0.0 <= score <= 5.0
        # otd = (18/20)*5 = 4.5, accident = (1-0/20)*5 = 5.0, pod = (15/15)*5 = 5.0
        # score = 4.5*0.4 + 5.0*0.3 + 5.0*0.3 = 1.8 + 1.5 + 1.5 = 4.8
        assert score == 4.8

    def test_최소건수_미달(self) -> None:
        """UT-TMS-023: 최소 건수 미달 시 None."""
        service, _repos = _make_service()
        score = service.calculate_carrier_performance(
            total_delivered=5,
            on_time_count=5,
            accident_count=0,
            pod_required_count=5,
            pod_submitted_count=5,
            min_shipments=10,
        )
        assert score is None
