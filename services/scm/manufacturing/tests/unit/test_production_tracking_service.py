"""생산 추적 서비스(ProductionTrackingService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_manufacturing_app.services.production_tracking_service import _parse_period


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_manufacturing_app.services.production_tracking_service.generate_name",
        side_effect=lambda prefix, **kw: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch(
        "oneerp_manufacturing_app.services.production_tracking_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_manufacturing_app.services.production_tracking_service import (
            ProductionTrackingService,
        )

        service = ProductionTrackingService(tenant_id="test-tenant")
    return (
        service,
        repos["work_orders"],
        repos["process_losses"],
        repos["oee_metrics"],
        repos["downtime_entries"],
        repos["production_variance_analyses"],
    )


class Test진행률:
    def test_진행률_계산(self) -> None:
        """produced / planned x 100 으로 진행률 계산."""
        service, wo_repo, *_ = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "planned_qty": 100,
            "produced_qty": 75,
        }

        result = service.get_progress("WO-001")

        assert result["progress_pct"] == 75.0

    def test_미존재_작업지시_에러(self) -> None:
        """작업지시 미존재 시 OneERPError(ERR-MFG-003)."""
        service, wo_repo, *_ = _make_service()
        wo_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="ERR-MFG-003"):
            service.get_progress("WO-999")


class Test공정손실:
    def test_손실_기록(self) -> None:
        """예상-실제 차이를 손실로 기록한다."""
        service, *_ = _make_service()

        result = service.record_process_loss("WO-001", "MAT-1", 100, 95)

        assert result["loss_qty"] == 5
        assert result["loss_percentage"] == 5.0

    def test_손실률_0_경계(self) -> None:
        """예상 수량 0이면 손실률 0."""
        service, *_ = _make_service()

        result = service.record_process_loss("WO-001", "MAT-1", 0, 0)

        assert result["loss_percentage"] == 0.0


class TestOEE:
    def test_OEE_산출(self) -> None:
        """가용률 x 성능률 x 양품률 = OEE."""
        service, wo_repo, _loss, _oee, downtime_repo, _var = _make_service()
        # 비가동 1000분 → 가용률 = (10560-1000)/10560
        downtime_repo.find_many.return_value = [
            {"duration_minutes": 1000},
        ]
        wo_repo.find_many.return_value = [
            {"planned_qty": 100, "produced_qty": 90, "process_loss_qty": 5},
        ]

        result = service.calculate_oee("WS-001", "2026-03")

        # 가용률 9560/10560, 성능률 0.9, 양품률 (90-5)/90
        assert result["availability"] > 0.9
        assert result["performance"] == 0.9
        assert result["quality_rate"] > 0.94
        assert result["oee"] > 0

    def test_OEE_날짜범위_필터_사용(self) -> None:
        """period 필터 대신 start_time/planned_start_date 날짜 범위를 사용한다."""
        service, wo_repo, _loss, _oee, downtime_repo, _var = _make_service()
        downtime_repo.find_many.return_value = []
        wo_repo.find_many.return_value = []

        service.calculate_oee("WS-001", "2026-03")

        # downtime 필터에 start_time 날짜 범위가 사용되어야 함
        dt_filter = downtime_repo.find_many.call_args[0][0]
        assert "start_time" in dt_filter
        assert dt_filter["start_time"] == {"$gte": "2026-03-01", "$lte": "2026-03-31"}
        assert "period" not in dt_filter

        # work_order 필터에 planned_start_date 날짜 범위가 사용되어야 함
        wo_filter = wo_repo.find_many.call_args[0][0]
        assert "planned_start_date" in wo_filter
        assert wo_filter["planned_start_date"] == {"$gte": "2026-03-01", "$lte": "2026-03-31"}
        assert "period" not in wo_filter

    def test_작업없으면_OEE_0(self) -> None:
        """해당 기간 작업이 없으면 성능·양품률 0."""
        service, wo_repo, _loss, _oee, downtime_repo, _var = _make_service()
        downtime_repo.find_many.return_value = []
        wo_repo.find_many.return_value = []

        result = service.calculate_oee("WS-001", "2026-03")

        assert result["oee"] == 0

    def test_분기_기간_필터(self) -> None:
        """분기(Q1~Q4) 형식 period를 올바른 날짜 범위로 변환한다."""
        service, wo_repo, _loss, _oee, downtime_repo, _var = _make_service()
        downtime_repo.find_many.return_value = []
        wo_repo.find_many.return_value = []

        service.calculate_oee("WS-001", "2026-Q1")

        dt_filter = downtime_repo.find_many.call_args[0][0]
        assert dt_filter["start_time"] == {"$gte": "2026-01-01", "$lte": "2026-03-31"}


class Test기간파싱:
    def test_월형식(self) -> None:
        """YYYY-MM 형식을 해당 월 1일~말일로 변환한다."""
        start, end = _parse_period("2026-03")
        assert start == "2026-03-01"
        assert end == "2026-03-31"

    def test_2월_윤년(self) -> None:
        """윤년 2월은 29일까지."""
        _start, end = _parse_period("2024-02")
        assert end == "2024-02-29"

    def test_2월_평년(self) -> None:
        """평년 2월은 28일까지."""
        _start, end = _parse_period("2025-02")
        assert end == "2025-02-28"

    def test_분기_Q1(self) -> None:
        """Q1 = 1월~3월."""
        start, end = _parse_period("2026-Q1")
        assert start == "2026-01-01"
        assert end == "2026-03-31"

    def test_분기_Q4(self) -> None:
        """Q4 = 10월~12월."""
        start, end = _parse_period("2026-Q4")
        assert start == "2026-10-01"
        assert end == "2026-12-31"

    def test_잘못된_형식_현재월(self) -> None:
        """인식할 수 없는 형식이면 현재 월 범위를 반환한다."""
        start, _end = _parse_period("invalid")
        # 현재 월의 1일로 시작해야 함
        assert start.endswith("-01")


class Test차이분석:
    def test_계획초과_생산(self) -> None:
        """생산이 계획 초과하면 양의 차이."""
        service, wo_repo, *_ = _make_service()
        wo_repo.find_by_id.return_value = {
            "_id": "WO-001",
            "planned_qty": 100,
            "produced_qty": 120,
        }

        result = service.analyze_variance("WO-001")

        assert result["variance"] == 20
        assert result["variance_percentage"] == 20.0
