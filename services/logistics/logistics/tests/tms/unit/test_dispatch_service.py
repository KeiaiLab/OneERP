"""배차 서비스(DispatchService) 단위 테스트.

UT-TMS-011~018, UT-TMS-024~025 커버.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """DispatchService와 mock Repository를 생성한다."""
    with patch("oneerp_logistics_app.tms.services.dispatch_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_logistics_app.tms.services.dispatch_service import DispatchService

        service = DispatchService(tenant_id="test-tenant")
    return service, repos


class Test차량적재량검증:
    """BR-TMS-002: 차량 적재량 검증."""

    def test_적재량_초과_에러(self) -> None:
        """UT-TMS-011: 10% 초과 시 에러."""
        service, repos = _make_service()
        repos["vehicles"].find_by_id.return_value = {
            "_id": "VHC-001",
            "max_weight_kg": 5000,
            "status": "available",
            "temperature_type": "normal",
        }

        with pytest.raises(OneERPError, match="ERR-TMS-102"):
            service.validate_vehicle("VHC-001", total_weight_kg=5600)

    def test_적재량_10퍼센트_이내_경고만(self) -> None:
        """UT-TMS-012: 10% 이내 초과 시 경고만 (에러 아님)."""
        service, repos = _make_service()
        repos["vehicles"].find_by_id.return_value = {
            "_id": "VHC-001",
            "max_weight_kg": 5000,
            "status": "available",
            "temperature_type": "normal",
        }

        # 5400kg = 8% 초과 → 경고만
        result = service.validate_vehicle("VHC-001", total_weight_kg=5400)
        assert result["_id"] == "VHC-001"


class Test운송사검증:
    """BR-TMS-003: 운송사 활성 검증."""

    def test_비활성_운송사_에러(self) -> None:
        """UT-TMS-013: 비활성 운송사 에러."""
        service, repos = _make_service()
        repos["carriers"].find_by_id.return_value = {
            "_id": "CRR-001",
            "is_active": False,
        }

        with pytest.raises(OneERPError, match="ERR-TMS-103"):
            service.validate_carrier("CRR-001")

    def test_활성_운송사_정상(self) -> None:
        """운송사 검증 정상 통과."""
        service, repos = _make_service()
        repos["carriers"].find_by_id.return_value = {
            "_id": "CRR-001",
            "is_active": True,
        }

        result = service.validate_carrier("CRR-001")
        assert result["_id"] == "CRR-001"


class Test차량가용상태:
    """BR-TMS-004: 차량 가용 상태 검증."""

    def test_비가용_차량_에러(self) -> None:
        """UT-TMS-014: 가용 상태가 아닌 차량 에러."""
        service, repos = _make_service()
        repos["vehicles"].find_by_id.return_value = {
            "_id": "VHC-001",
            "max_weight_kg": 5000,
            "status": "in_transit",
            "temperature_type": "normal",
        }

        with pytest.raises(OneERPError, match="ERR-TMS-104"):
            service.validate_vehicle("VHC-001")


class Test온도차량매칭:
    """BR-TMS-009: 온도 차량 매칭."""

    def test_냉장_요구_냉장_차량(self) -> None:
        """UT-TMS-015: 냉장 요구 → 냉장 차량 매칭."""
        service, repos = _make_service()
        repos["vehicles"].find_by_id.return_value = {
            "_id": "VHC-002",
            "max_weight_kg": 3000,
            "status": "available",
            "temperature_type": "refrigerated",
        }

        result = service.validate_vehicle("VHC-002", temperature_requirement="refrigerated")
        assert result["_id"] == "VHC-002"

    def test_냉장_요구_일반_차량_에러(self) -> None:
        """UT-TMS-015: 냉장 요구 → 일반 차량 에러."""
        service, repos = _make_service()
        repos["vehicles"].find_by_id.return_value = {
            "_id": "VHC-003",
            "max_weight_kg": 5000,
            "status": "available",
            "temperature_type": "normal",
        }

        with pytest.raises(OneERPError, match="ERR-TMS-106"):
            service.validate_vehicle("VHC-003", temperature_requirement="refrigerated")


class Test중복배차방지:
    """BR-TMS-012: 배송 건 중복 배차 방지."""

    def test_이미_배차된_건_에러(self) -> None:
        """UT-TMS-016: 이미 배차된 배송 건 재배차 시 에러."""
        service, repos = _make_service()
        repos["shipments"].find_by_id.return_value = {
            "_id": "SHP-001",
            "status": "dispatched",
            "delivery_order_id": "DO-001",
        }

        with pytest.raises(OneERPError, match="ERR-TMS-107"):
            service.validate_shipments_for_dispatch(["SHP-001"])


class TestPOD필수검증:
    """BR-TMS-007: POD 필수 검증."""

    def test_pod_필수_확인(self) -> None:
        """UT-TMS-018: requires_pod=true 확인."""
        service, repos = _make_service()
        repos["delivery_conditions"].find_by_id.return_value = {
            "_id": "DC-001",
            "requires_pod": True,
        }

        result = service.check_pod_required({"delivery_condition_id": "DC-001"})
        assert result is True

    def test_pod_불필요(self) -> None:
        """requires_pod=false 확인."""
        service, repos = _make_service()
        repos["delivery_conditions"].find_by_id.return_value = {
            "_id": "DC-002",
            "requires_pod": False,
        }

        result = service.check_pod_required({"delivery_condition_id": "DC-002"})
        assert result is False


class Test상태전이:
    """상태 전이 검증 테스트."""

    def test_유효한_배송건_전이(self) -> None:
        """draft → pending 허용."""
        service, _repos = _make_service()
        service.validate_shipment_transition("draft", "pending")

    def test_무효한_배송건_전이(self) -> None:
        """draft → delivered 불허."""
        service, _repos = _make_service()
        with pytest.raises(OneERPError, match="ERR-TMS-109"):
            service.validate_shipment_transition("draft", "delivered")

    def test_유효한_배차_전이(self) -> None:
        """draft → confirmed 허용."""
        service, _repos = _make_service()
        service.validate_do_transition("draft", "confirmed")

    def test_무효한_배차_전이(self) -> None:
        """completed → draft 불허."""
        service, _repos = _make_service()
        with pytest.raises(OneERPError, match="ERR-TMS-109"):
            service.validate_do_transition("completed", "draft")


class Test자동배차:
    """BR-TMS-017: 자동 배차 그룹핑."""

    def test_지역_그룹핑(self) -> None:
        """UT-TMS-024: 동일 경로 통합."""
        service, _repos = _make_service()
        shipments = [
            {"_id": "SHP-001", "ship_from": {"address": "서울"}, "ship_to": {"address": "부산"}},
            {"_id": "SHP-002", "ship_from": {"address": "서울"}, "ship_to": {"address": "부산"}},
            {"_id": "SHP-003", "ship_from": {"address": "서울"}, "ship_to": {"address": "대전"}},
        ]

        groups = service.group_shipments_by_route(shipments)
        assert len(groups) == 2
        assert len(groups["서울→부산"]) == 2
        assert len(groups["서울→대전"]) == 1

    def test_반품사유필수(self) -> None:
        """UT-TMS-017: 반품 사유 미입력 검증은 모델 레벨에서 처리."""
        from oneerp_logistics_app.tms.models.return_shipment import ReturnShipmentCreate
        from oneerp_logistics_app.tms.models.shipment import ShipAddress
        from pydantic import ValidationError

        # return_reason이 필수 필드이므로 누락 시 ValidationError
        with pytest.raises(ValidationError, match="return_reason"):
            ReturnShipmentCreate(
                pickup_from=ShipAddress(name="test"),
                return_to=ShipAddress(name="test"),
                return_reason="defective",
                items=[],
            )
