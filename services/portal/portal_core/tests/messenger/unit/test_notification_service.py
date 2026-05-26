"""알림 서비스(NotificationService) 단위 테스트.

SC-MSG-020: 알림 생성 정상 시나리오.
SC-MSG-021: 알림 읽음 처리.
SC-MSG-022: 일괄 읽음 처리.
SC-MSG-023: 미읽은 알림 수 조회.
EX-MSG-020: 유효하지 않은 알림 유형 에러.
EX-MSG-021: 타인 알림 읽음 처리 에러.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_portal_core_app.messenger.services.notification_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """NotificationService + mock 리포지터리를 생성한다."""
    with patch(
        "oneerp_portal_core_app.messenger.services.notification_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_portal_core_app.messenger.services.notification_service import (
            NotificationService,
        )

        service = NotificationService(tenant_id="test-tenant")
    return service, repos


class Test알림생성:
    """SC-MSG-020: 알림 생성 시나리오."""

    def test_멘션_알림_생성(self) -> None:
        """SC-MSG-020: 멘션 유형 알림 정상 생성."""
        service, repos = _make_service()

        result = service.create_notification(
            user_id="USER-001",
            notification_type="mention",
            title="멘션 알림",
            body="USER-002님이 당신을 멘션했습니다",
            reference_id="MSG-001",
            channel_id="CH-001",
        )

        assert result["notification_id"] == "NTF-001"
        assert result["notification_type"] == "mention"
        assert result["is_read"] is False
        repos["notifications"].insert.assert_called_once()

    def test_유효하지_않은_알림_유형(self) -> None:
        """EX-MSG-020: 유효하지 않은 알림 유형 → ERR-MSG-020."""
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="ERR-MSG-020"):
            service.create_notification(
                user_id="USER-001",
                notification_type="invalid_type",
                title="테스트",
            )


class Test알림읽음처리:
    """SC-MSG-021, EX-MSG-021."""

    def test_알림_읽음_처리(self) -> None:
        """SC-MSG-021: 정상 읽음 처리."""
        service, repos = _make_service()
        repos["notifications"].find_by_id.return_value = {
            "_id": "NTF-001",
            "user_id": "USER-001",
            "is_read": False,
        }

        result = service.mark_as_read("NTF-001", "USER-001")

        assert result["is_read"] is True
        assert result["already_read"] is False
        repos["notifications"].update_by_id.assert_called_once()

    def test_이미_읽은_알림(self) -> None:
        """이미 읽은 알림은 already_read=True."""
        service, repos = _make_service()
        repos["notifications"].find_by_id.return_value = {
            "_id": "NTF-001",
            "user_id": "USER-001",
            "is_read": True,
        }

        result = service.mark_as_read("NTF-001", "USER-001")

        assert result["already_read"] is True

    def test_타인_알림_읽음_에러(self) -> None:
        """EX-MSG-021: 타인의 알림 읽음 처리 → ERR-MSG-022."""
        service, repos = _make_service()
        repos["notifications"].find_by_id.return_value = {
            "_id": "NTF-001",
            "user_id": "USER-001",
            "is_read": False,
        }

        with pytest.raises(ValueError, match="ERR-MSG-022"):
            service.mark_as_read("NTF-001", "USER-999")

    def test_존재하지_않는_알림(self) -> None:
        """존재하지 않는 알림 읽음 처리 → ERR-MSG-030."""
        service, repos = _make_service()
        repos["notifications"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="ERR-MSG-030"):
            service.mark_as_read("NTF-999", "USER-001")


class Test일괄읽음:
    """SC-MSG-022: 일괄 읽음 처리."""

    def test_일괄_읽음_처리(self) -> None:
        """SC-MSG-022: 미읽은 알림 3건 일괄 읽음."""
        service, repos = _make_service()
        repos["notifications"].find_many.return_value = [
            {"_id": "NTF-001", "is_read": False},
            {"_id": "NTF-002", "is_read": False},
            {"_id": "NTF-003", "is_read": False},
        ]

        result = service.mark_all_as_read("USER-001")

        assert result["marked_count"] == 3


class Test미읽은수:
    """SC-MSG-023: 미읽은 알림 수 조회."""

    def test_미읽은_알림_수(self) -> None:
        service, repos = _make_service()
        repos["notifications"].find_many.return_value = [
            {"_id": "NTF-001"},
            {"_id": "NTF-002"},
        ]

        result = service.get_unread_count("USER-001")

        assert result["unread_count"] == 2
