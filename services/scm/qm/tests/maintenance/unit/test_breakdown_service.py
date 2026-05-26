"""고장보전 서비스(BreakdownService) 단위 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_qm_app.maintenance.services.breakdown_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """서비스 인스턴스와 mock 리포지토리를 생성한다."""
    with patch("oneerp_qm_app.maintenance.services.breakdown_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_qm_app.maintenance.services.breakdown_service import BreakdownService

        service = BreakdownService(tenant_id="test-tenant")
    return (
        service,
        repos["breakdown_reports"],
        repos["work_orders"],
        repos["equipments"],
    )


def _sample_breakdown(**overrides: object) -> dict:
    """테스트용 고장신고 데이터."""
    base: dict = {
        "_id": "BR-001",
        "equipment_id": "EQ-001",
        "reported_by": "김기사",
        "failure_mode": "모터 과열",
        "severity": "major",
        "status": "reported",
        "description": "1호기 모터에서 이상 과열 발생",
    }
    base.update(overrides)
    return base


def _sample_work_order(**overrides: object) -> dict:
    """테스트용 작업지시 데이터."""
    base: dict = {
        "_id": "WO-001",
        "equipment_id": "EQ-001",
        "status": "in_progress",
        "breakdown_report_id": "BR-001",
        "work_order_type": "corrective",
    }
    base.update(overrides)
    return base


def _sample_equipment(**overrides: object) -> dict:
    """테스트용 설비 데이터."""
    base: dict = {
        "_id": "EQ-001",
        "equipment_name": "1호 프레스 기계",
        "status": "under_maintenance",
        "failure_count": 2,
    }
    base.update(overrides)
    return base


class Test고장작업지시생성:
    """고장신고로부터 작업지시 생성 테스트."""

    def test_정상_생성(self) -> None:
        """고장신고로부터 작업지시가 정상 생성된다."""
        service, br_repo, wo_repo, _equip_repo = _make_service()
        br_repo.find_by_id.return_value = _sample_breakdown()

        result = service.create_work_order_from_breakdown("BR-001")

        assert result["work_order_id"] == "WO-001"
        assert result["breakdown_report_id"] == "BR-001"
        assert result["equipment_id"] == "EQ-001"
        assert result["priority"] == "high"  # major → high
        wo_repo.insert.assert_called_once()
        br_repo.update_by_id.assert_called_once()

    def test_심각도별_우선순위_매핑(self) -> None:
        """고장 심각도에 따라 작업지시 우선순위가 결정된다."""
        # critical → critical
        service, br_repo, _wo_repo, _equip_repo = _make_service()
        br_repo.find_by_id.return_value = _sample_breakdown(severity="critical")

        result = service.create_work_order_from_breakdown("BR-001")
        assert result["priority"] == "critical"

    def test_minor_심각도(self) -> None:
        """minor 심각도는 low 우선순위로 매핑된다."""
        service, br_repo, _wo_repo, _equip_repo = _make_service()
        br_repo.find_by_id.return_value = _sample_breakdown(severity="minor")

        result = service.create_work_order_from_breakdown("BR-001")
        assert result["priority"] == "low"

    def test_설비_상태_변경(self) -> None:
        """작업지시 생성 시 설비 상태가 under_maintenance로 변경된다."""
        service, br_repo, _wo_repo, equip_repo = _make_service()
        br_repo.find_by_id.return_value = _sample_breakdown()

        service.create_work_order_from_breakdown("BR-001")

        equip_repo.update_by_id.assert_called_once_with(
            "EQ-001",
            {"status": "under_maintenance"},
        )

    def test_고장신고_미존재(self) -> None:
        """존재하지 않는 고장신고는 ValueError를 발생시킨다."""
        service, br_repo, _wo_repo, _equip_repo = _make_service()
        br_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.create_work_order_from_breakdown("BR-999")

    def test_이미_처리된_고장신고(self) -> None:
        """이미 작업지시가 생성된 고장신고는 ValueError를 발생시킨다."""
        service, br_repo, _wo_repo, _equip_repo = _make_service()
        br_repo.find_by_id.return_value = _sample_breakdown(status="work_order_created")

        with pytest.raises(ValueError, match="작업지시를 생성할 수 없습니다"):
            service.create_work_order_from_breakdown("BR-001")


class Test작업지시완료:
    """작업지시 완료 처리 테스트."""

    def test_정상_완료(self) -> None:
        """작업지시가 정상적으로 완료 처리된다."""
        service, _br_repo, wo_repo, equip_repo = _make_service()
        wo_repo.find_by_id.return_value = _sample_work_order()
        equip_repo.find_by_id.return_value = _sample_equipment()

        result = service.complete_work_order(
            "WO-001",
            labor_hours=4.0,
            material_cost=Decimal(50000),
            labor_cost=Decimal(80000),
            root_cause="베어링 마모",
            resolution="베어링 교체",
        )

        assert result["status"] == "completed"
        assert result["labor_hours"] == 4.0
        assert result["total_cost"] == "130000"
        wo_repo.update_by_id.assert_called_once()

    def test_고장신고_상태_변경(self) -> None:
        """완료 시 연관 고장신고가 resolved로 변경된다."""
        service, br_repo, wo_repo, equip_repo = _make_service()
        wo_repo.find_by_id.return_value = _sample_work_order()
        equip_repo.find_by_id.return_value = _sample_equipment()

        service.complete_work_order("WO-001")

        # 고장신고 상태 업데이트 확인
        br_repo.update_by_id.assert_called_once()
        call_args = br_repo.update_by_id.call_args
        assert call_args[0][0] == "BR-001"
        assert call_args[0][1]["status"] == "resolved"

    def test_설비_상태_복원_및_고장횟수_증가(self) -> None:
        """완료 시 설비 상태가 active로 복원되고 고장 횟수가 증가한다."""
        service, _br_repo, wo_repo, equip_repo = _make_service()
        wo_repo.find_by_id.return_value = _sample_work_order()
        equip_repo.find_by_id.return_value = _sample_equipment(failure_count=2)

        service.complete_work_order("WO-001")

        equip_repo.update_by_id.assert_called_once_with(
            "EQ-001",
            {"status": "active", "failure_count": 3},
        )

    def test_작업지시_미존재(self) -> None:
        """존재하지 않는 작업지시는 ValueError를 발생시킨다."""
        service, _br_repo, wo_repo, _equip_repo = _make_service()
        wo_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.complete_work_order("WO-999")

    def test_이미_완료된_작업지시(self) -> None:
        """이미 완료된 작업지시는 ValueError를 발생시킨다."""
        service, _br_repo, wo_repo, _equip_repo = _make_service()
        wo_repo.find_by_id.return_value = _sample_work_order(status="completed")

        with pytest.raises(ValueError, match="완료 처리할 수 없습니다"):
            service.complete_work_order("WO-001")

    def test_고장신고_없는_작업지시_완료(self) -> None:
        """고장신고가 없는 작업지시도 정상 완료된다."""
        service, br_repo, wo_repo, equip_repo = _make_service()
        wo_repo.find_by_id.return_value = _sample_work_order(breakdown_report_id="")
        equip_repo.find_by_id.return_value = _sample_equipment()

        result = service.complete_work_order("WO-001")

        assert result["status"] == "completed"
        br_repo.update_by_id.assert_not_called()
        # 고장신고 없으므로 failure_count 증가 안 함
        equip_repo.update_by_id.assert_called_once_with(
            "EQ-001",
            {"status": "active"},
        )
