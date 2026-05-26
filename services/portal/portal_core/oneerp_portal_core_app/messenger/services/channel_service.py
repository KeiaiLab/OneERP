"""채널 서비스 — 채널 생성, 멤버 관리, 아카이브 비즈니스 로직.

BR-MSG-001: 채널명은 2~100자 이내.
BR-MSG-002: 채널 유형은 public/private/direct 중 하나.
BR-MSG-003: direct 채널은 정확히 2명의 멤버만 허용.
BR-MSG-004: 아카이브된 채널에는 메시지를 보낼 수 없다.
BR-MSG-005: 채널 소유자만 채널을 아카이브할 수 있다.
BR-MSG-006: 중복 채널명(동일 tenant 내)은 허용하지 않는다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ChannelService:
    """채널 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._channel_repo = Repository("channels", tenant_id=tenant_id)
        self._message_repo = Repository("messages", tenant_id=tenant_id)

    def create_channel(
        self,
        channel_name: str,
        channel_type: str,
        owner_id: str,
        members: list[str] | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """채널을 생성한다.

        BR-MSG-001: 채널명은 2~100자 이내.
        BR-MSG-003: direct 채널은 정확히 2명의 멤버.
        BR-MSG-006: 중복 채널명 금지.

        Raises:
            ValueError: 비즈니스 규칙 위반 시 (ERR-MSG-001 ~ ERR-MSG-006)
        """
        members = members or []

        # BR-MSG-001: 채널명 길이 검증
        if len(channel_name) < 2 or len(channel_name) > 100:
            msg = "ERR-MSG-001: 채널명은 2~100자 이내여야 합니다"
            raise ValueError(msg)

        # BR-MSG-003: direct 채널 멤버 수 검증
        if channel_type == "direct" and len(members) != 2:
            msg = "ERR-MSG-003: 1:1 채널은 정확히 2명의 멤버가 필요합니다"
            raise ValueError(msg)

        # BR-MSG-006: 동일 tenant 내 중복 채널명 검증 (direct 제외)
        if channel_type != "direct":
            existing = self._channel_repo.find_many(
                {"channel_name": channel_name, "status": "active"},
                limit=1,
            )
            if existing:
                msg = f"ERR-MSG-006: 채널명 '{channel_name}'이 이미 존재합니다"
                raise ValueError(msg)

        # 소유자를 멤버에 자동 포함
        if owner_id and owner_id not in members:
            members.append(owner_id)

        channel_id = generate_name("CH", tenant_id=self._tenant_id)
        self._channel_repo.insert(
            {
                "_id": channel_id,
                "channel_name": channel_name,
                "channel_type": channel_type,
                "description": description,
                "owner_id": owner_id,
                "members": members,
                "status": "active",
                "pinned_message_ids": [],
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("채널 생성: %s (유형: %s, 멤버: %d명)", channel_id, channel_type, len(members))
        return {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "channel_type": channel_type,
            "member_count": len(members),
            "status": "active",
        }

    def add_member(self, channel_id: str, user_id: str) -> dict[str, Any]:
        """채널에 멤버를 추가한다.

        BR-MSG-004: 아카이브된 채널에는 멤버 추가 불가.

        Raises:
            ValueError: 채널 미존재 또는 아카이브 상태 (ERR-MSG-004)
        """
        channel = self._channel_repo.find_by_id(channel_id)
        if not channel:
            msg = f"ERR-MSG-010: 채널 '{channel_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if channel.get("status") == "archived":
            msg = "ERR-MSG-004: 아카이브된 채널에는 멤버를 추가할 수 없습니다"
            raise ValueError(msg)

        members = channel.get("members", [])
        if user_id in members:
            return {"channel_id": channel_id, "user_id": user_id, "already_member": True}

        members.append(user_id)
        self._channel_repo.update_by_id(channel_id, {"members": members})

        logger.info("채널 멤버 추가: %s → %s", user_id, channel_id)
        return {"channel_id": channel_id, "user_id": user_id, "already_member": False}

    def remove_member(self, channel_id: str, user_id: str) -> dict[str, Any]:
        """채널에서 멤버를 제거한다.

        Raises:
            ValueError: 채널 미존재 (ERR-MSG-010)
        """
        channel = self._channel_repo.find_by_id(channel_id)
        if not channel:
            msg = f"ERR-MSG-010: 채널 '{channel_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        members = channel.get("members", [])
        if user_id not in members:
            return {"channel_id": channel_id, "user_id": user_id, "removed": False}

        members.remove(user_id)
        self._channel_repo.update_by_id(channel_id, {"members": members})

        logger.info("채널 멤버 제거: %s ← %s", user_id, channel_id)
        return {"channel_id": channel_id, "user_id": user_id, "removed": True}

    def archive_channel(self, channel_id: str, requester_id: str) -> dict[str, Any]:
        """채널을 아카이브한다.

        BR-MSG-005: 채널 소유자만 아카이브 가능.

        Raises:
            ValueError: 권한 없음 또는 채널 미존재 (ERR-MSG-005)
        """
        channel = self._channel_repo.find_by_id(channel_id)
        if not channel:
            msg = f"ERR-MSG-010: 채널 '{channel_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if channel.get("owner_id") != requester_id:
            msg = "ERR-MSG-005: 채널 소유자만 아카이브할 수 있습니다"
            raise ValueError(msg)

        self._channel_repo.update_by_id(channel_id, {"status": "archived"})
        logger.info("채널 아카이브: %s (요청자: %s)", channel_id, requester_id)
        return {"channel_id": channel_id, "status": "archived"}

    def create_channel_from_request(self, body: Any) -> dict[str, Any]:
        """ChannelCreate 요청 바디를 받아 단순 채널을 생성한다.

        Route 레이어의 얇은 CRUD 위임용. BR-MSG 비즈니스 룰 검증은
        Pydantic 스키마(ChannelCreate) 레벨에서 이미 처리됨.
        """
        channel_id = generate_name("CH", tenant_id=self._tenant_id)
        doc = body.model_dump()
        doc["_id"] = channel_id
        doc["tenant_id"] = self._tenant_id
        self._channel_repo.insert(doc)
        logger.info("채널 생성(단순): %s", channel_id)
        return {"channel_id": channel_id, "message": "채널이 생성되었습니다"}

    def list_channels(self, skip: int, limit: int) -> dict[str, Any]:
        """채널 목록을 페이지네이션으로 조회한다."""
        data = self._channel_repo.find_many(skip=skip, limit=limit, sort=[("created_at", -1)])
        total = self._channel_repo.count()
        return {"data": data, "total": total}

    def get_channel(self, doc_id: str) -> dict[str, Any] | None:
        """채널 상세를 조회한다."""
        return self._channel_repo.find_by_id(doc_id)

    def update_channel_fields(self, doc_id: str, update_data: dict[str, Any]) -> bool:
        """채널을 수정한다. 채널이 존재하면 True, 없으면 False."""
        doc = self._channel_repo.find_by_id(doc_id)
        if not doc:
            return False
        self._channel_repo.update_by_id(doc_id, update_data)
        return True

    def delete_channel(self, doc_id: str) -> bool:
        """채널을 삭제한다. 존재하면 True, 없으면 False."""
        doc = self._channel_repo.find_by_id(doc_id)
        if not doc:
            return False
        self._channel_repo.delete_by_id(doc_id)
        return True

    def pin_message(self, channel_id: str, message_id: str) -> dict[str, Any]:
        """채널에 메시지를 고정한다.

        Raises:
            ValueError: 채널 미존재 (ERR-MSG-010)
        """
        channel = self._channel_repo.find_by_id(channel_id)
        if not channel:
            msg = f"ERR-MSG-010: 채널 '{channel_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        pinned = channel.get("pinned_message_ids", [])
        if message_id in pinned:
            return {"channel_id": channel_id, "message_id": message_id, "already_pinned": True}

        pinned.append(message_id)
        self._channel_repo.update_by_id(channel_id, {"pinned_message_ids": pinned})

        logger.info("메시지 고정: %s → 채널 %s", message_id, channel_id)
        return {"channel_id": channel_id, "message_id": message_id, "already_pinned": False}
