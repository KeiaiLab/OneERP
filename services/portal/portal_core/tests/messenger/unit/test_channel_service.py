"""채널 서비스(ChannelService) 단위 테스트.

SC-MSG-001: 공개 채널 생성 정상 시나리오.
SC-MSG-002: 1:1(direct) 채널 생성 — 멤버 2명.
SC-MSG-003: 채널명 길이 위반 에러.
SC-MSG-004: direct 채널 멤버 수 위반 에러.
SC-MSG-005: 중복 채널명 에러.
EX-MSG-001: 아카이브된 채널 멤버 추가 에러.
EX-MSG-002: 소유자가 아닌 사용자의 아카이브 시도 에러.
EX-MSG-003: 메시지 고정.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_portal_core_app.messenger.services.channel_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """ChannelService + mock 리포지터리를 생성한다."""
    with patch(
        "oneerp_portal_core_app.messenger.services.channel_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_portal_core_app.messenger.services.channel_service import ChannelService

        service = ChannelService(tenant_id="test-tenant")
    return service, repos


class Test채널생성:
    """SC-MSG-001 ~ SC-MSG-005: 채널 생성 시나리오."""

    def test_공개_채널_생성(self) -> None:
        """SC-MSG-001: 공개 채널 정상 생성."""
        service, repos = _make_service()
        repos["channels"].find_many.return_value = []

        result = service.create_channel(
            channel_name="일반",
            channel_type="public",
            owner_id="USER-001",
            members=["USER-001", "USER-002"],
        )

        assert result["channel_id"] == "CH-001"
        assert result["channel_type"] == "public"
        assert result["member_count"] == 2
        repos["channels"].insert.assert_called_once()

    def test_direct_채널_생성(self) -> None:
        """SC-MSG-002: 1:1 채널 정상 생성."""
        service, _repos = _make_service()

        result = service.create_channel(
            channel_name="DM-USER1-USER2",
            channel_type="direct",
            owner_id="USER-001",
            members=["USER-001", "USER-002"],
        )

        assert result["channel_type"] == "direct"
        assert result["member_count"] == 2

    def test_채널명_길이_위반(self) -> None:
        """SC-MSG-003: 채널명이 2자 미만이면 ERR-MSG-001."""
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="ERR-MSG-001"):
            service.create_channel(
                channel_name="X",
                channel_type="public",
                owner_id="USER-001",
            )

    def test_direct_채널_멤버수_위반(self) -> None:
        """SC-MSG-004: direct 채널에 3명 → ERR-MSG-003."""
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="ERR-MSG-003"):
            service.create_channel(
                channel_name="DM",
                channel_type="direct",
                owner_id="USER-001",
                members=["USER-001", "USER-002", "USER-003"],
            )

    def test_중복_채널명(self) -> None:
        """SC-MSG-005: 동일 tenant 내 중복 채널명 → ERR-MSG-006."""
        service, repos = _make_service()
        repos["channels"].find_many.return_value = [{"_id": "CH-EXIST", "channel_name": "일반"}]

        with pytest.raises(ValueError, match="ERR-MSG-006"):
            service.create_channel(
                channel_name="일반",
                channel_type="public",
                owner_id="USER-001",
            )

    def test_소유자_자동_멤버_포함(self) -> None:
        """소유자가 멤버 목록에 없으면 자동 추가."""
        service, repos = _make_service()
        repos["channels"].find_many.return_value = []

        result = service.create_channel(
            channel_name="개발팀",
            channel_type="private",
            owner_id="USER-001",
            members=["USER-002"],
        )

        assert result["member_count"] == 2


class Test채널멤버관리:
    """EX-MSG-001: 아카이브 채널 멤버 추가 에러."""

    def test_아카이브_채널_멤버추가_에러(self) -> None:
        """EX-MSG-001: 아카이브된 채널에 멤버 추가 시 ERR-MSG-004."""
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "archived",
            "members": ["USER-001"],
        }

        with pytest.raises(ValueError, match="ERR-MSG-004"):
            service.add_member("CH-001", "USER-002")

    def test_멤버_정상_추가(self) -> None:
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "active",
            "members": ["USER-001"],
        }

        result = service.add_member("CH-001", "USER-002")

        assert result["already_member"] is False
        repos["channels"].update_by_id.assert_called_once()

    def test_멤버_제거(self) -> None:
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "status": "active",
            "members": ["USER-001", "USER-002"],
        }

        result = service.remove_member("CH-001", "USER-002")

        assert result["removed"] is True


class Test채널아카이브:
    """EX-MSG-002: 소유자가 아닌 사용자의 아카이브 시도."""

    def test_소유자_아카이브(self) -> None:
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "owner_id": "USER-001",
            "status": "active",
        }

        result = service.archive_channel("CH-001", "USER-001")

        assert result["status"] == "archived"

    def test_비소유자_아카이브_에러(self) -> None:
        """EX-MSG-002: 소유자가 아닌 사용자가 아카이브 → ERR-MSG-005."""
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "owner_id": "USER-001",
            "status": "active",
        }

        with pytest.raises(ValueError, match="ERR-MSG-005"):
            service.archive_channel("CH-001", "USER-999")


class Test메시지고정:
    """EX-MSG-003: 메시지 고정."""

    def test_메시지_고정(self) -> None:
        service, repos = _make_service()
        repos["channels"].find_by_id.return_value = {
            "_id": "CH-001",
            "pinned_message_ids": [],
        }

        result = service.pin_message("CH-001", "MSG-001")

        assert result["already_pinned"] is False
        repos["channels"].update_by_id.assert_called_once()
