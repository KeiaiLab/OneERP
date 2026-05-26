"""조직 트리 서비스(OrgTreeService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_portal_comms_app.directory.services.org_tree_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """OrgTreeService와 관련 Repository mock을 생성한다."""
    with patch(
        "oneerp_portal_comms_app.directory.services.org_tree_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_portal_comms_app.directory.services.org_tree_service import OrgTreeService

        service = OrgTreeService(tenant_id="test-tenant")
    return service, repos


class Test조직트리조회:
    def test_조직_트리_정상조회(self) -> None:
        """활성 조직 단위로 트리를 구성한다."""
        service, repos = _make_service()
        repos["organizations"].find_by_id.return_value = {
            "_id": "ORG-001",
            "org_name": "테스트법인",
        }
        repos["org_units"].find_many.return_value = [
            {
                "_id": "UNIT-001",
                "unit_code": "DIV01",
                "unit_name": "경영본부",
                "unit_type": "division",
                "parent_unit_id": None,
                "sort_order": 1,
            },
            {
                "_id": "UNIT-002",
                "unit_code": "DEPT01",
                "unit_name": "인사팀",
                "unit_type": "department",
                "parent_unit_id": "UNIT-001",
                "sort_order": 1,
            },
        ]

        result = service.get_org_tree("ORG-001")

        assert result["org_id"] == "ORG-001"
        assert result["total_units"] == 2
        assert len(result["units"]) == 1  # 루트 노드 1개
        assert result["units"][0]["unit_name"] == "경영본부"
        assert len(result["units"][0]["children"]) == 1
        assert result["units"][0]["children"][0]["unit_name"] == "인사팀"

    def test_조직_미존재_에러(self) -> None:
        """존재하지 않는 조직 조회 시 ValueError를 발생시킨다."""
        service, repos = _make_service()
        repos["organizations"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="ERR-DIR-001"):
            service.get_org_tree("ORG-999")

    def test_빈_트리(self) -> None:
        """조직 단위가 없으면 빈 트리를 반환한다."""
        service, repos = _make_service()
        repos["organizations"].find_by_id.return_value = {
            "_id": "ORG-001",
            "org_name": "테스트법인",
        }
        repos["org_units"].find_many.return_value = []

        result = service.get_org_tree("ORG-001")

        assert result["total_units"] == 0
        assert result["units"] == []


class Test순환참조방지:
    def test_자기자신_참조_에러(self) -> None:
        """자기 자신을 상위로 설정하면 에러를 발생시킨다."""
        service, _ = _make_service()

        with pytest.raises(ValueError, match="ERR-DIR-013"):
            service.validate_no_circular_reference("UNIT-001", "UNIT-001")

    def test_정상_부모_변경(self) -> None:
        """순환이 없는 경우 True를 반환한다."""
        service, repos = _make_service()
        repos["org_units"].find_by_id.return_value = {
            "_id": "UNIT-002",
            "parent_unit_id": None,
        }

        result = service.validate_no_circular_reference("UNIT-001", "UNIT-002")
        assert result is True

    def test_순환_참조_감지(self) -> None:
        """A→B→A 순환 참조를 감지한다."""
        service, repos = _make_service()
        # UNIT-002의 부모가 UNIT-001 → 순환
        repos["org_units"].find_by_id.return_value = {
            "_id": "UNIT-002",
            "parent_unit_id": "UNIT-001",
        }

        with pytest.raises(ValueError, match="ERR-DIR-013"):
            service.validate_no_circular_reference("UNIT-001", "UNIT-002")


class Test조직단위이동:
    def test_이동_성공(self) -> None:
        """조직 단위를 다른 상위로 이동한다."""
        service, repos = _make_service()
        repos["org_units"].find_by_id.side_effect = [
            # move_unit → find_by_id(unit_id)
            {
                "_id": "UNIT-003",
                "parent_unit_id": "UNIT-001",
            },
            # validate → find_by_id(new_parent_id)
            {
                "_id": "UNIT-002",
                "parent_unit_id": None,
            },
        ]

        result = service.move_unit("UNIT-003", "UNIT-002")

        assert result["unit_id"] == "UNIT-003"
        assert result["old_parent_id"] == "UNIT-001"
        assert result["new_parent_id"] == "UNIT-002"
        repos["org_units"].update_by_id.assert_called_once()

    def test_미존재_단위_이동_에러(self) -> None:
        """존재하지 않는 단위를 이동하면 에러를 발생시킨다."""
        service, repos = _make_service()
        repos["org_units"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="ERR-DIR-005"):
            service.move_unit("UNIT-999", "UNIT-001")


class Test스냅샷:
    def test_스냅샷_생성(self) -> None:
        """조직도 스냅샷을 정상적으로 생성한다."""
        service, repos = _make_service()
        repos["organizations"].find_by_id.return_value = {
            "_id": "ORG-001",
            "org_name": "테스트법인",
        }
        repos["org_units"].find_many.return_value = [
            {"_id": "UNIT-001", "unit_name": "본부", "parent_unit_id": None},
        ]
        repos["employee_directories"].find_many.return_value = [
            {"_id": "EDIR-001", "employee_name": "홍길동"},
            {"_id": "EDIR-002", "employee_name": "김철수"},
        ]

        from datetime import date

        result = service.create_snapshot("ORG-001", snapshot_date=date(2026, 3, 29))

        assert result["snapshot_id"] == "SNAP-001"
        assert result["total_units"] == 1
        assert result["total_employees"] == 2
        repos["org_chart_snapshots"].insert.assert_called_once()
