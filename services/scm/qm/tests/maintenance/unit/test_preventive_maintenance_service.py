"""예방보전 서비스(PreventiveMaintenanceService) 단위 테스트."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_qm_app.maintenance.services.preventive_maintenance_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """서비스 인스턴스와 mock 리포지토리를 생성한다."""
    with patch(
        "oneerp_qm_app.maintenance.services.preventive_maintenance_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_qm_app.maintenance.services.preventive_maintenance_service import (
            PreventiveMaintenanceService,
        )

        service = PreventiveMaintenanceService(tenant_id="test-tenant")
    return (
        service,
        repos["preventive_maintenance_plans"],
        repos["work_orders"],
        repos["equipments"],
    )


def _sample_plan(**overrides: object) -> dict:
    """테스트용 예방보전계획 데이터."""
    base: dict = {
        "_id": "PMP-001",
        "plan_name": "컨베이어 벨트 월간 점검",
        "equipment_id": "EQ-001",
        "interval_days": 30,
        "is_active": True,
        "assigned_team": "보전1팀",
        "description": "월간 정기 점검",
        "next_due_date": date(2026, 3, 1),
        "start_date": date(2026, 1, 1),
    }
    base.update(overrides)
    return base


def _sample_equipment(**overrides: object) -> dict:
    """테스트용 설비 데이터."""
    base = {
        "_id": "EQ-001",
        "equipment_name": "1호 컨베이어 벨트",
        "status": "active",
    }
    base.update(overrides)
    return base


class Test작업지시자동생성:
    """예방보전계획 기반 작업지시 자동 생성 테스트."""

    def test_기한_도래_시_작업지시_생성(self) -> None:
        """기한이 도래한 계획에 대해 작업지시가 생성된다."""
        service, plan_repo, wo_repo, equip_repo = _make_service()
        plan_repo.find_many.return_value = [_sample_plan()]
        equip_repo.find_by_id.return_value = _sample_equipment()

        results = service.generate_work_orders(target_date=date(2026, 3, 1))

        assert len(results) == 1
        assert results[0]["work_order_id"] == "WO-001"
        assert results[0]["plan_id"] == "PMP-001"
        assert results[0]["equipment_id"] == "EQ-001"
        wo_repo.insert.assert_called_once()
        plan_repo.update_by_id.assert_called_once()

    def test_다음_예정일_업데이트(self) -> None:
        """작업지시 생성 후 다음 예정일이 interval_days만큼 뒤로 밀린다."""
        service, plan_repo, _wo_repo, equip_repo = _make_service()
        plan_repo.find_many.return_value = [_sample_plan(interval_days=14)]
        equip_repo.find_by_id.return_value = _sample_equipment()

        results = service.generate_work_orders(target_date=date(2026, 3, 1))

        expected_next = date(2026, 3, 1) + timedelta(days=14)
        assert results[0]["next_due_date"] == expected_next
        plan_repo.update_by_id.assert_called_once_with(
            "PMP-001",
            {
                "last_execution_date": date(2026, 3, 1),
                "next_due_date": expected_next,
            },
        )

    def test_기한_미도래_시_건너뜀(self) -> None:
        """기한이 아직 도래하지 않은 계획은 건너뛴다."""
        service, plan_repo, wo_repo, _equip_repo = _make_service()
        plan_repo.find_many.return_value = [_sample_plan(next_due_date=date(2026, 4, 1))]

        results = service.generate_work_orders(target_date=date(2026, 3, 1))

        assert len(results) == 0
        wo_repo.insert.assert_not_called()

    def test_비활성_계획_제외(self) -> None:
        """비활성 계획은 조회되지 않는다 (find_many 쿼리 필터 확인)."""
        service, plan_repo, _wo_repo, _equip_repo = _make_service()
        plan_repo.find_many.return_value = []

        results = service.generate_work_orders(target_date=date(2026, 3, 1))

        assert len(results) == 0
        plan_repo.find_many.assert_called_once_with({"is_active": True}, limit=10000)

    def test_설비_미존재_시_건너뜀(self) -> None:
        """설비가 존재하지 않는 계획은 건너뛴다."""
        service, plan_repo, wo_repo, equip_repo = _make_service()
        plan_repo.find_many.return_value = [_sample_plan()]
        equip_repo.find_by_id.return_value = None

        results = service.generate_work_orders(target_date=date(2026, 3, 1))

        assert len(results) == 0
        wo_repo.insert.assert_not_called()


class Test기한도래계획조회:
    """향후 기한 도래 예방보전계획 조회 테스트."""

    def test_기간_내_계획_반환(self) -> None:
        """기준일로부터 N일 이내 기한인 계획을 반환한다."""
        service, plan_repo, _wo_repo, _equip_repo = _make_service()
        plan_repo.find_many.return_value = [
            _sample_plan(
                _id="PMP-A",
                next_due_date=date(2026, 3, 3),
            ),
            _sample_plan(
                _id="PMP-B",
                next_due_date=date(2026, 3, 7),
            ),
        ]

        results = service.get_upcoming_plans(
            days_ahead=7,
            reference_date=date(2026, 3, 1),
        )

        assert len(results) == 2

    def test_기간_초과_계획_제외(self) -> None:
        """기준일로부터 N일을 초과하는 계획은 제외된다."""
        service, plan_repo, _wo_repo, _equip_repo = _make_service()
        plan_repo.find_many.return_value = [
            _sample_plan(
                _id="PMP-FAR",
                next_due_date=date(2026, 4, 1),
            ),
        ]

        results = service.get_upcoming_plans(
            days_ahead=7,
            reference_date=date(2026, 3, 1),
        )

        assert len(results) == 0
