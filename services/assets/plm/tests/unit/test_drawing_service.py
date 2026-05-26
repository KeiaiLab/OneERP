"""도면 서비스(DrawingService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """서비스와 mock 저장소를 생성한다."""
    with patch("oneerp_plm_app.services.drawing_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_plm_app.services.drawing_service import DrawingService

        service = DrawingService(tenant_id="test-tenant")
    return service, repos


class Test도면체크아웃:
    """도면 체크아웃 테스트."""

    def test_정상_체크아웃(self) -> None:
        """도면을 체크아웃할 수 있다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "status": "work_in_progress",
            "checked_out_by": None,
        }

        result = service.checkout("DWG-001", "USR-001")

        assert result["checked_out_by"] == "USR-001"
        repos["drawings"].update_by_id.assert_called_once()

    def test_이미_체크아웃된_도면(self) -> None:
        """이미 체크아웃된 도면을 다시 체크아웃할 수 없다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "status": "work_in_progress",
            "checked_out_by": "USR-002",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.checkout("DWG-001", "USR-001")
        assert exc_info.value.status_code == 409

    def test_폐기된_도면_체크아웃_실패(self) -> None:
        """폐기된 도면은 체크아웃할 수 없다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "status": "obsolete",
            "checked_out_by": None,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.checkout("DWG-001", "USR-001")
        assert "폐기된" in (exc_info.value.detail or "")

    def test_미존재_도면_체크아웃_실패(self) -> None:
        """존재하지 않는 도면은 체크아웃할 수 없다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.checkout("DWG-999", "USR-001")
        assert exc_info.value.status_code == 404


class Test도면체크인:
    """도면 체크인 테스트."""

    def test_정상_체크인_리비전_증가(self) -> None:
        """체크인 시 리비전이 A → B로 증가한다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "revision": "A",
            "checked_out_by": "USR-001",
            "revision_history": [],
        }

        result = service.checkin(
            "DWG-001", "USR-001", "https://files/new.dwg", "new.dwg", 1024, "변경사항"
        )

        assert result["previous_revision"] == "A"
        assert result["new_revision"] == "B"
        repos["drawings"].update_by_id.assert_called_once()

    def test_다른_사용자_체크인_실패(self) -> None:
        """체크아웃한 사용자가 아닌 사람은 체크인할 수 없다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "revision": "A",
            "checked_out_by": "USR-002",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.checkin("DWG-001", "USR-001", "url", "f", 100)
        assert exc_info.value.status_code == 403

    def test_체크아웃_안된_도면_체크인_실패(self) -> None:
        """체크아웃 상태가 아닌 도면은 체크인할 수 없다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "revision": "A",
            "checked_out_by": None,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.checkin("DWG-001", "USR-001", "url", "f", 100)
        assert "체크아웃 상태가 아닌" in (exc_info.value.detail or "")


class Test도면릴리즈:
    """도면 릴리즈 테스트."""

    def test_정상_릴리즈(self) -> None:
        """도면을 릴리즈할 수 있다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "status": "work_in_progress",
            "checked_out_by": None,
        }

        result = service.release("DWG-001", "USR-001")

        assert result["status"] == "released"
        repos["drawings"].update_by_id.assert_called_once()

    def test_체크아웃_상태_릴리즈_실패(self) -> None:
        """체크아웃 상태의 도면은 릴리즈할 수 없다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "status": "work_in_progress",
            "checked_out_by": "USR-002",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.release("DWG-001", "USR-001")
        assert "체크아웃 상태" in (exc_info.value.detail or "")

    def test_폐기된_도면_릴리즈_실패(self) -> None:
        """폐기된 도면은 릴리즈할 수 없다."""
        service, repos = _make_service()
        repos["drawings"].find_by_id.return_value = {
            "_id": "DWG-001",
            "status": "obsolete",
            "checked_out_by": None,
        }

        with pytest.raises(OneERPError) as exc_info:
            service.release("DWG-001", "USR-001")
        assert "폐기된" in (exc_info.value.detail or "")


class Test리비전증가:
    """리비전 증가 로직 테스트."""

    def test_A에서_B로(self) -> None:
        """A → B."""
        from oneerp_plm_app.services.drawing_service import _next_revision

        assert _next_revision("A") == "B"

    def test_Y에서_Z로(self) -> None:
        """Y → Z."""
        from oneerp_plm_app.services.drawing_service import _next_revision

        assert _next_revision("Y") == "Z"

    def test_Z에서_AA로(self) -> None:
        """Z → AA."""
        from oneerp_plm_app.services.drawing_service import _next_revision

        assert _next_revision("Z") == "AA"
