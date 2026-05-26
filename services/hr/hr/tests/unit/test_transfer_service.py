"""인사이동 서비스(TransferService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_hr_app.services.transfer_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_hr_app.services.transfer_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_hr_app.services.transfer_service import TransferService

        service = TransferService(tenant_id="test-tenant")
    return service, repos["employee_transfers"], repos["employees"]


class Test인사이동:
    def test_부서이동(self) -> None:
        service, transfer_repo, emp_repo = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-001",
            "department": "개발팀",
            "designation": "과장",
        }

        result = service.execute_transfer("EMP-001", new_department="기획팀", reason="조직개편")

        assert result["transfer_id"] == "ETR-001"
        assert result["changes"]["department"]["from"] == "개발팀"
        assert result["changes"]["department"]["to"] == "기획팀"
        transfer_repo.insert.assert_called_once()
        # 직원 마스터 갱신 + outbox 이벤트 기록 = 2회 호출
        assert emp_repo.update_by_id.call_count == 2

    def test_직위변경(self) -> None:
        service, _transfer, emp_repo = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-001",
            "department": "개발팀",
            "designation": "과장",
        }

        result = service.execute_transfer("EMP-001", new_designation="차장")

        assert result["changes"]["designation"]["to"] == "차장"

    def test_직원_미존재_에러(self) -> None:
        service, _transfer, emp_repo = _make_service()
        emp_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.execute_transfer("EMP-999", new_department="기획팀")
        assert exc_info.value.status_code == 404
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_부서이동_시_EMPLOYEE_UPDATED_이벤트_발행(self) -> None:
        """BR-HR-009: 인사이동 시 EMPLOYEE_UPDATED 이벤트가 _outbox에 기록된다."""
        service, _transfer, emp_repo = _make_service()
        emp_repo.find_by_id.return_value = {
            "_id": "EMP-001",
            "department": "개발팀",
            "designation": "과장",
        }

        result = service.execute_transfer("EMP-001", new_department="기획팀", reason="조직개편")

        # update_by_id가 2번 호출: 1) 직원 마스터 갱신, 2) outbox 이벤트 기록
        assert emp_repo.update_by_id.call_count == 2

        # 두 번째 호출이 outbox 이벤트
        outbox_call = emp_repo.update_by_id.call_args_list[1]
        assert outbox_call == call(
            "EMP-001", {"$push": {"_outbox": outbox_call[0][1]["$push"]["_outbox"]}}
        )

        outbox_entry = outbox_call[0][1]["$push"]["_outbox"]
        assert outbox_entry["event_type"] == EventType.EMPLOYEE_UPDATED.value
        assert outbox_entry["doc_id"] == "EMP-001"
        assert outbox_entry["data"]["department"] == "기획팀"
        assert outbox_entry["data"]["designation"] == "과장"
        assert outbox_entry["data"]["transfer_id"] == result["transfer_id"]

    def test_변경사항_없으면_에러(self) -> None:
        service, _transfer, emp_repo = _make_service()
        emp_repo.find_by_id.return_value = {"_id": "EMP-001"}

        with pytest.raises(OneERPError) as exc_info:
            service.execute_transfer("EMP-001")
        assert exc_info.value.status_code == 422
        assert "1개 이상 변경" in (exc_info.value.detail or "")
