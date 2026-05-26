"""교대 배정 서비스(ShiftService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    with patch("oneerp_hr_app.services.shift_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_hr_app.services.shift_service import ShiftService

        service = ShiftService(tenant_id="test-tenant")
    return service, repos["shift_assignments"], repos["attendances"]


class Test교대조회:
    def test_교대_배정_조회(self) -> None:
        service, shift_repo, _att = _make_service()
        shift_repo.find_many.return_value = [
            {"_id": "SA-001", "employee": "EMP-001", "shift_type": "주간"}
        ]

        result = service.get_employee_shift("EMP-001", "2026-03-20")

        assert result is not None
        assert result["shift_type"] == "주간"

    def test_배정없으면_None(self) -> None:
        service, shift_repo, _att = _make_service()
        shift_repo.find_many.return_value = []

        result = service.get_employee_shift("EMP-001", "2026-03-20")

        assert result is None


class Test출석준수율:
    def test_100퍼센트_준수(self) -> None:
        service, shift_repo, att_repo = _make_service()
        shift_repo.find_many.return_value = [{"_id": "SA-001"}, {"_id": "SA-002"}]
        att_repo.find_many.return_value = [{"_id": "ATT-001"}, {"_id": "ATT-002"}]

        result = service.check_attendance_compliance("EMP-001", "2026-03-01", "2026-03-31")

        assert result["compliance_rate"] == 100.0
        assert result["absent_days"] == 0

    def test_50퍼센트_준수(self) -> None:
        service, shift_repo, att_repo = _make_service()
        shift_repo.find_many.return_value = [{"_id": f"SA-{i}"} for i in range(4)]
        att_repo.find_many.return_value = [{"_id": "ATT-001"}, {"_id": "ATT-002"}]

        result = service.check_attendance_compliance("EMP-001", "2026-03-01", "2026-03-31")

        assert result["compliance_rate"] == 50.0
        assert result["absent_days"] == 2

    def test_배정없으면_0퍼센트(self) -> None:
        service, shift_repo, att_repo = _make_service()
        shift_repo.find_many.return_value = []
        att_repo.find_many.return_value = []

        result = service.check_attendance_compliance("EMP-001", "2026-03-01", "2026-03-31")

        assert result["compliance_rate"] == 0.0
