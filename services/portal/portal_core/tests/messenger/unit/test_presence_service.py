"""프레즌스 서비스(PresenceService) 단위 테스트.

SC-MSG-040: 프레즌스 업데이트 정상 시나리오.
SC-MSG-041: 프레즌스 조회.
SC-MSG-042: 일괄 프레즌스 조회.
EX-MSG-040: 유효하지 않은 상태 에러.
EX-MSG-041: 상태 메시지 200자 초과 에러.
EX-MSG-042: 오프라인 전환 시 last_seen_at 기록.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_portal_core_app.messenger.services.presence_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """PresenceService + mock 리포지터리를 생성한다."""
    with patch(
        "oneerp_portal_core_app.messenger.services.presence_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_portal_core_app.messenger.services.presence_service import PresenceService

        service = PresenceService(tenant_id="test-tenant")
    return service, repos


class Test프레즌스업데이트:
    """SC-MSG-040: 프레즌스 업데이트 시나리오."""

    def test_온라인_상태_업데이트(self) -> None:
        """SC-MSG-040: 온라인 상태 정상 업데이트."""
        service, repos = _make_service()
        repos["user_presences"].find_many.return_value = []

        result = service.update_presence("USER-001", "online", "업무중")

        assert result["status"] == "online"
        assert result["status_message"] == "업무중"
        repos["user_presences"].insert.assert_called_once()

    def test_기존_프레즌스_업데이트(self) -> None:
        """기존 프레즌스가 있으면 update."""
        service, repos = _make_service()
        repos["user_presences"].find_many.return_value = [
            {"_id": "PRS-001", "user_id": "USER-001", "status": "online"}
        ]

        result = service.update_presence("USER-001", "away")

        assert result["status"] == "away"
        repos["user_presences"].update_by_id.assert_called_once()

    def test_오프라인_전환_last_seen(self) -> None:
        """EX-MSG-042: 오프라인 전환 시 last_seen_at 기록."""
        service, repos = _make_service()
        repos["user_presences"].find_many.return_value = [
            {"_id": "PRS-001", "user_id": "USER-001", "status": "online"}
        ]

        service.update_presence("USER-001", "offline")

        call_args = repos["user_presences"].update_by_id.call_args
        assert "last_seen_at" in call_args[0][1]

    def test_유효하지_않은_상태(self) -> None:
        """EX-MSG-040: 유효하지 않은 상태 → ERR-MSG-040."""
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="ERR-MSG-040"):
            service.update_presence("USER-001", "invalid_status")

    def test_상태_메시지_길이_초과(self) -> None:
        """EX-MSG-041: 상태 메시지 201자 → ERR-MSG-041."""
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="ERR-MSG-041"):
            service.update_presence("USER-001", "online", "가" * 201)


class Test프레즌스조회:
    """SC-MSG-041: 프레즌스 조회."""

    def test_프레즌스_조회(self) -> None:
        """SC-MSG-041: 기존 프레즌스 조회."""
        service, repos = _make_service()
        repos["user_presences"].find_many.return_value = [
            {
                "_id": "PRS-001",
                "user_id": "USER-001",
                "status": "online",
                "status_message": "업무중",
                "last_seen_at": None,
            }
        ]

        result = service.get_presence("USER-001")

        assert result["status"] == "online"

    def test_프레즌스_미존재시_오프라인(self) -> None:
        """프레즌스 기록이 없으면 offline 기본값."""
        service, repos = _make_service()
        repos["user_presences"].find_many.return_value = []

        result = service.get_presence("USER-999")

        assert result["status"] == "offline"


class Test일괄프레즌스조회:
    """SC-MSG-042: 일괄 프레즌스 조회."""

    def test_일괄_조회(self) -> None:
        service, repos = _make_service()
        repos["user_presences"].find_many.side_effect = [
            [
                {
                    "_id": "PRS-001",
                    "user_id": "USER-001",
                    "status": "online",
                    "status_message": "",
                    "last_seen_at": None,
                }
            ],
            [
                {
                    "_id": "PRS-002",
                    "user_id": "USER-002",
                    "status": "away",
                    "status_message": "",
                    "last_seen_at": None,
                }
            ],
        ]

        result = service.get_bulk_presence(["USER-001", "USER-002"])

        assert result["total"] == 2
        assert result["presences"][0]["status"] == "online"
        assert result["presences"][1]["status"] == "away"
