"""생산능력 계획 서비스(CapacityPlanningService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_manufacturing_app.services.capacity_planning_service.generate_name",
        side_effect=lambda prefix, **kw: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch(
        "oneerp_manufacturing_app.services.capacity_planning_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_manufacturing_app.services.capacity_planning_service import (
            CapacityPlanningService,
        )

        service = CapacityPlanningService(tenant_id="test-tenant")
    return service, repos["capacity_plans"], repos["work_orders"]


class Test가용시간산출:
    def test_계획_있으면_잔여시간(self) -> None:
        """기존 계획에서 planned_hours를 차감한다."""
        service, plan_repo, _wo = _make_service()
        plan_repo.find_many.return_value = [
            {"available_hours": 176, "planned_hours": 100},
        ]

        result = service.calculate_available_capacity("WS-001", "2026-03")

        assert result["available_hours"] == 76

    def test_계획_없으면_기본값(self) -> None:
        """계획이 없으면 기본 176시간."""
        service, plan_repo, _wo = _make_service()
        plan_repo.find_many.return_value = []

        result = service.calculate_available_capacity("WS-001", "2026-03")

        assert result["total_hours"] == 176
        assert result["available_hours"] == 176

    def test_초과계획_시_0반환(self) -> None:
        """planned_hours > available_hours이면 가용시간 0."""
        service, plan_repo, _wo = _make_service()
        plan_repo.find_many.return_value = [
            {"available_hours": 100, "planned_hours": 150},
        ]

        result = service.calculate_available_capacity("WS-001", "2026-03")

        assert result["available_hours"] == 0


class Test계획생성:
    def test_생산능력_계획_생성(self) -> None:
        """계획 문서를 생성하고 저장한다."""
        service, plan_repo, _wo = _make_service()

        result = service.create_capacity_plan("WS-001", "2026-03", 200)

        assert result["workstation_id"] == "WS-001"
        assert result["available_hours"] == 200
        assert result["planned_hours"] == 0
        plan_repo.insert.assert_called_once()


class Test충돌검사:
    def test_용량_충분하면_충돌없음(self) -> None:
        """가용 시간이 충분하면 has_conflict=False."""
        service, plan_repo, _wo = _make_service()
        plan_repo.find_many.return_value = [
            {"available_hours": 176, "planned_hours": 50},
        ]

        result = service.check_capacity_conflict("WS-001", 100, "2026-03")

        assert result["has_conflict"] is False
        assert result["surplus_or_deficit"] == 26

    def test_용량_초과하면_충돌(self) -> None:
        """가용 시간 초과 시 has_conflict=True."""
        service, plan_repo, _wo = _make_service()
        plan_repo.find_many.return_value = [
            {"available_hours": 176, "planned_hours": 150},
        ]

        result = service.check_capacity_conflict("WS-001", 50, "2026-03")

        assert result["has_conflict"] is True
        assert result["surplus_or_deficit"] == -24
