"""메시지 서비스(MessageService) 단위 테스트.

SC-MSG-010: 메시지 전송 정상 시나리오.
SC-MSG-011: 답글 메시지 전송.
SC-MSG-012: 메시지 수정.
SC-MSG-013: 메시지 삭제 (소프트 삭제).
SC-MSG-014: 리액션 추가.
EX-MSG-010: 아카이브 채널 메시지 전송 에러.
EX-MSG-011: 비멤버 메시지 전송 에러.
EX-MSG-012: 타인 메시지 수정 에러.
EX-MSG-013: 타인 메시지 삭제 에러.
EX-MSG-014: 삭제된 메시지 수정 에러.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_portal_core_app.messenger.services.message_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """MessageService + mock 리포지터리를 생성한다."""
    with patch(
        "oneerp_portal_core_app.messenger.services.message_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_portal_core_app.messenger.services.message_service import MessageService

        service = MessageService(tenant_id="test-tenant")
    return service, repos


class Test메시지전송:
    """SC-MSG-010 ~ SC-MSG-011: 메시지 전송 시나리오."""

    def test_텍스트_메시지_전송(self) -> None:
        """SC-MSG-010: 텍스트 메시지 정상 전송."""
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "active",
            "members": ["USER-001", "USER-002"],
        }

        result = service.send_message(
            channel_id="CH-001",
            sender_id="USER-001",
            content="안녕하세요!",
        )

        assert result["message_id"] == "MSG-001"
        assert result["status"] == "active"
        repos["messages"].insert.assert_called_once()

    def test_답글_메시지_전송(self) -> None:
        """SC-MSG-011: 답글 메시지 정상 전송 + 스레드 생성."""
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "active",
            "members": ["USER-001"],
        }
        repos["threads"].find_many.return_value = []

        result = service.send_message(
            channel_id="CH-001",
            sender_id="USER-001",
            content="답글입니다",
            message_type="reply",
            parent_message_id="MSG-PARENT",
        )

        assert result["message_type"] == "reply"
        repos["threads"].insert.assert_called_once()

    def test_빈_본문_에러(self) -> None:
        """메시지 본문이 비어있으면 ERR-MSG-010."""
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="ERR-MSG-010"):
            service.send_message(
                channel_id="CH-001",
                sender_id="USER-001",
                content="",
            )

    def test_reply_유형_parent_없음_에러(self) -> None:
        """답글 유형인데 parent_message_id가 없으면 ERR-MSG-012."""
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "active",
            "members": ["USER-001"],
        }

        with pytest.raises(ValueError, match="ERR-MSG-012"):
            service.send_message(
                channel_id="CH-001",
                sender_id="USER-001",
                content="답글",
                message_type="reply",
            )

    def test_아카이브_채널_전송_에러(self) -> None:
        """EX-MSG-010: 아카이브된 채널에 전송 → ERR-MSG-014."""
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "archived",
            "members": ["USER-001"],
        }

        with pytest.raises(ValueError, match="ERR-MSG-014"):
            service.send_message(
                channel_id="CH-001",
                sender_id="USER-001",
                content="메시지",
            )

    def test_비멤버_전송_에러(self) -> None:
        """EX-MSG-011: 채널 멤버가 아닌 사용자 전송 → ERR-MSG-015."""
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "active",
            "members": ["USER-001"],
        }

        with pytest.raises(ValueError, match="ERR-MSG-015"):
            service.send_message(
                channel_id="CH-001",
                sender_id="USER-999",
                content="메시지",
            )


class Test메시지수정:
    """SC-MSG-012, EX-MSG-012, EX-MSG-014."""

    def test_메시지_수정(self) -> None:
        """SC-MSG-012: 본인 메시지 수정."""
        service, repos = _make_service()
        repos["messages"].find_by_id.return_value = {
            "_id": "MSG-001",
            "sender_id": "USER-001",
            "content": "원본",
            "status": "active",
        }

        result = service.edit_message("MSG-001", "USER-001", "수정본")

        assert result["status"] == "edited"
        repos["messages"].update_by_id.assert_called_once()

    def test_타인_메시지_수정_에러(self) -> None:
        """EX-MSG-012: 타인 메시지 수정 → ERR-MSG-016."""
        service, repos = _make_service()
        repos["messages"].find_by_id.return_value = {
            "_id": "MSG-001",
            "sender_id": "USER-001",
            "status": "active",
        }

        with pytest.raises(ValueError, match="ERR-MSG-016"):
            service.edit_message("MSG-001", "USER-999", "수정 시도")

    def test_삭제된_메시지_수정_에러(self) -> None:
        """EX-MSG-014: 삭제된 메시지 수정 → ERR-MSG-013."""
        service, repos = _make_service()
        repos["messages"].find_by_id.return_value = {
            "_id": "MSG-001",
            "sender_id": "USER-001",
            "status": "deleted",
        }

        with pytest.raises(ValueError, match="ERR-MSG-013"):
            service.edit_message("MSG-001", "USER-001", "수정 시도")


class Test메시지삭제:
    """SC-MSG-013, EX-MSG-013."""

    def test_메시지_삭제(self) -> None:
        """SC-MSG-013: 소프트 삭제 — 본문이 대체된다."""
        service, repos = _make_service()
        repos["messages"].find_by_id.return_value = {
            "_id": "MSG-001",
            "sender_id": "USER-001",
            "status": "active",
        }

        result = service.delete_message("MSG-001", "USER-001")

        assert result["status"] == "deleted"
        call_args = repos["messages"].update_by_id.call_args
        assert call_args[0][1]["content"] == "(삭제된 메시지)"

    def test_타인_메시지_삭제_에러(self) -> None:
        """EX-MSG-013: 타인 메시지 삭제 → ERR-MSG-016."""
        service, repos = _make_service()
        repos["messages"].find_by_id.return_value = {
            "_id": "MSG-001",
            "sender_id": "USER-001",
            "status": "active",
        }

        with pytest.raises(ValueError, match="ERR-MSG-016"):
            service.delete_message("MSG-001", "USER-999")


class Test리액션:
    """SC-MSG-014: 리액션 추가."""

    def test_리액션_추가(self) -> None:
        """SC-MSG-014: 정상 리액션 추가."""
        service, repos = _make_service()
        repos["messages"].find_by_id.return_value = {
            "_id": "MSG-001",
            "reactions": [],
        }

        result = service.add_reaction("MSG-001", "USER-001", "👍")

        assert result["already_reacted"] is False
        repos["messages"].update_by_id.assert_called_once()

    def test_중복_리액션(self) -> None:
        """동일 사용자+이모지 중복 리액션은 무시."""
        service, repos = _make_service()
        repos["messages"].find_by_id.return_value = {
            "_id": "MSG-001",
            "reactions": [{"user_id": "USER-001", "emoji": "👍"}],
        }

        result = service.add_reaction("MSG-001", "USER-001", "👍")

        assert result["already_reacted"] is True
