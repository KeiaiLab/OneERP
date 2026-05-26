"""안전 사고 통계 서비스(IncidentStatsService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """IncidentStatsService와 mock 레포지토리를 생성한다."""
    with patch("oneerp_ehs_app.services.incident_stats_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_ehs_app.services.incident_stats_service import IncidentStatsService

        service = IncidentStatsService(tenant_id="test-tenant")
    return service, repos["safety_incidents"]


class Test사고통계:
    """안전 사고 통계 테스트."""

    def test_빈_통계(self) -> None:
        """사고가 없으면 빈 통계를 반환한다."""
        service, repo = _make_service()
        repo.find_many.return_value = []

        result = service.get_statistics()

        assert result["total_incidents"] == 0
        assert result["kosha_reported"] == 0
        assert result["by_type"] == {}

    def test_유형별_집계(self) -> None:
        """사고 유형별로 올바르게 집계한다."""
        service, repo = _make_service()
        repo.find_many.return_value = [
            {"incident_type": "injury", "severity": "minor", "status": "closed"},
            {"incident_type": "injury", "severity": "major", "status": "investigating"},
            {"incident_type": "near_miss", "severity": "minor", "status": "closed"},
        ]

        result = service.get_statistics()

        assert result["total_incidents"] == 3
        assert result["by_type"]["injury"] == 2
        assert result["by_type"]["near_miss"] == 1

    def test_심각도별_집계(self) -> None:
        """심각도별로 올바르게 집계한다."""
        service, repo = _make_service()
        repo.find_many.return_value = [
            {"incident_type": "injury", "severity": "major", "status": "closed"},
            {"incident_type": "injury", "severity": "minor", "status": "closed"},
        ]

        result = service.get_statistics()

        assert result["by_severity"]["major"] == 1
        assert result["by_severity"]["minor"] == 1

    def test_안전공단_신고_집계(self) -> None:
        """안전공단 신고 건수를 올바르게 집계한다."""
        service, repo = _make_service()
        repo.find_many.return_value = [
            {
                "incident_type": "injury",
                "severity": "fatal",
                "status": "closed",
                "reported_to_kosha": True,
            },
            {
                "incident_type": "near_miss",
                "severity": "minor",
                "status": "closed",
                "reported_to_kosha": False,
            },
        ]

        result = service.get_statistics()

        assert result["kosha_reported"] == 1
