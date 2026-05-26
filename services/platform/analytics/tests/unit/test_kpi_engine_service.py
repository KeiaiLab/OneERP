"""KPI 엔진 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from oneerp_analytics_app.services.kpi_engine_service import KPIEngineService
from oneerp_core.errors import OneERPError


class TestKPIEngineService:
    """KPIEngineService 테스트."""

    def test_take_snapshot(self, mock_collection) -> None:
        """KPI 스냅샷을 기록하고 달성률을 계산한다."""
        mock_collection.find_one.return_value = {
            "_id": "KPID-2026-00001",
            "kpi_name": "매출",
            "target_value": 1000.0,
            "is_active": True,
            "tenant_id": "T1",
        }
        svc = KPIEngineService("T1")
        result = svc.take_snapshot("KPID-2026-00001", "2026-Q1", 800.0)
        assert result["achievement_rate"] == 80.0
        assert "snapshot_id" in result
        mock_collection.insert_one.assert_called_once()

    def test_take_snapshot_zero_target(self, mock_collection) -> None:
        """목표값이 0일 때 달성률은 0이다."""
        mock_collection.find_one.return_value = {
            "_id": "KPID-2026-00001",
            "target_value": 0.0,
            "tenant_id": "T1",
        }
        svc = KPIEngineService("T1")
        result = svc.take_snapshot("KPID-2026-00001", "2026-Q1", 500.0)
        assert result["achievement_rate"] == 0.0

    def test_take_snapshot_테넌트별_채번(self, mock_collection) -> None:
        """스냅샷 ID 채번은 서비스 tenant를 명시적으로 전달한다."""
        mock_collection.find_one.return_value = {
            "_id": "KPID-2026-00001",
            "target_value": 100.0,
            "tenant_id": "T1",
        }
        svc = KPIEngineService("T1")

        with patch(
            "oneerp_analytics_app.services.kpi_engine_service.generate_name",
            side_effect=lambda prefix, *, tenant_id=None: (
                "KPIS-2026-00001"
                if tenant_id == "T1"
                else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
            ),
        ) as mock_name:
            result = svc.take_snapshot("KPID-2026-00001", "2026-Q1", 80.0)

        assert result["snapshot_id"] == "KPIS-2026-00001"
        mock_name.assert_called_once_with("KPIS", tenant_id="T1")

    def test_take_snapshot_not_found(self, mock_collection) -> None:
        """존재하지 않는 KPI에 스냅샷 시 에러."""
        mock_collection.find_one.return_value = None
        svc = KPIEngineService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.take_snapshot("INVALID", "2026-Q1", 100.0)

    def test_get_trend(self, mock_collection) -> None:
        """최근 N기간 KPI 시계열을 반환한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value.sort.return_value = [
            {"kpi_id": "KPID-2026-00001", "period": "2026-Q1", "actual_value": 800.0},
            {"kpi_id": "KPID-2026-00001", "period": "2025-Q4", "actual_value": 750.0},
        ]
        svc = KPIEngineService("T1")
        result = svc.get_trend("KPID-2026-00001", periods=2)
        assert len(result) == 2

    def test_get_dashboard_summary(self, mock_collection) -> None:
        """활성 KPI의 기간별 요약을 반환한다."""
        from unittest.mock import MagicMock

        # find 호출마다 다른 cursor mock 반환
        cursor_kpi = MagicMock()
        cursor_kpi.skip.return_value.limit.return_value = [
            {
                "_id": "KPID-2026-00001",
                "kpi_name": "매출",
                "target_value": 1000.0,
                "is_active": True,
            },
        ]
        cursor_snapshot = MagicMock()
        cursor_snapshot.skip.return_value.limit.return_value = [
            {"kpi_id": "KPID-2026-00001", "actual_value": 800.0, "achievement_rate": 80.0},
        ]
        mock_collection.find.side_effect = [cursor_kpi, cursor_snapshot]

        svc = KPIEngineService("T1")
        summaries = svc.get_dashboard_summary("2026-Q1")
        assert len(summaries) == 1
        assert summaries[0]["kpi_name"] == "매출"

    def test_get_dashboard_summary_no_snapshot(self, mock_collection) -> None:
        """스냅샷이 없는 KPI는 actual_value=0으로 반환한다."""
        from unittest.mock import MagicMock

        cursor_kpi = MagicMock()
        cursor_kpi.skip.return_value.limit.return_value = [
            {
                "_id": "KPID-2026-00001",
                "kpi_name": "매출",
                "target_value": 1000.0,
                "is_active": True,
            },
        ]
        cursor_snapshot = MagicMock()
        cursor_snapshot.skip.return_value.limit.return_value = []
        mock_collection.find.side_effect = [cursor_kpi, cursor_snapshot]

        svc = KPIEngineService("T1")
        summaries = svc.get_dashboard_summary("2026-Q1")
        assert len(summaries) == 1
        assert summaries[0]["actual_value"] == 0.0
