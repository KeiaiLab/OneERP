"""메시지 서비스 — 메시지 전송, 수정, 삭제, 검색 비즈니스 로직.

BR-MSG-010: 메시지 본문은 1~10000자 이내.
BR-MSG-011: 메시지 유형은 text/file/system/reply 중 하나.
BR-MSG-012: reply 유형은 parent_message_id가 필수.
BR-MSG-013: 삭제된 메시지는 본문이 "(삭제된 메시지)"로 대체.
BR-MSG-014: 아카이브된 채널에는 메시지를 보낼 수 없다.
BR-MSG-015: 채널 멤버만 메시지를 보낼 수 있다.
BR-MSG-016: 본인이 보낸 메시지만 수정/삭제 가능.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_DELETED_CONTENT = "(삭제된 메시지)"


class MessageService:
    """메시지 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._message_repo = Repository("messages", tenant_id=tenant_id)
        self._channel_repo = Repository("channels", tenant_id=tenant_id)
        self._thread_repo = Repository("threads", tenant_id=tenant_id)

    def send_message(
        self,
        channel_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text",
        parent_message_id: str | None = None,
        file_url: str | None = None,
        file_name: str | None = None,
        mentions: list[str] | None = None,
    ) -> dict[str, Any]:
        """메시지를 전송한다.

        BR-MSG-010: 본문 1~10000자.
        BR-MSG-012: reply 유형은 parent_message_id 필수.
        BR-MSG-014: 아카이브된 채널에 전송 금지.
        BR-MSG-015: 채널 멤버만 전송 가능.

        Raises:
            ValueError: 비즈니스 규칙 위반 시 (ERR-MSG-010 ~ ERR-MSG-015)
        """
        mentions = mentions or []

        # BR-MSG-010: 본문 길이 검증
        if not content or len(content) > 10000:
            msg = "ERR-MSG-010: 메시지 본문은 1~10000자 이내여야 합니다"
            raise ValueError(msg)

        # BR-MSG-012: reply 유형은 parent_message_id 필수
        if message_type == "reply" and not parent_message_id:
            msg = "ERR-MSG-012: 답글 메시지는 parent_message_id가 필수입니다"
            raise ValueError(msg)

        # 채널 검증
        channel = self._channel_repo.find_by_id(channel_id)
        if not channel:
            msg = f"ERR-MSG-010: 채널 '{channel_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        # BR-MSG-014: 아카이브된 채널 검증
        if channel.get("status") == "archived":
            msg = "ERR-MSG-014: 아카이브된 채널에는 메시지를 보낼 수 없습니다"
            raise ValueError(msg)

        # BR-MSG-015: 멤버 검증
        members = channel.get("members", [])
        if sender_id not in members:
            msg = "ERR-MSG-015: 채널 멤버만 메시지를 보낼 수 있습니다"
            raise ValueError(msg)

        message_id = generate_name("MSG", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)

        self._message_repo.insert(
            {
                "_id": message_id,
                "channel_id": channel_id,
                "sender_id": sender_id,
                "content": content,
                "message_type": message_type,
                "status": "active",
                "parent_message_id": parent_message_id,
                "file_url": file_url,
                "file_name": file_name,
                "mentions": mentions,
                "reactions": [],
                "edited_at": None,
                "thread_count": 0,
                "created_at": now,
                "tenant_id": self._tenant_id,
            }
        )

        # 스레드 업데이트 (답글인 경우)
        if parent_message_id:
            self._update_thread(channel_id, parent_message_id, sender_id)

        logger.info("메시지 전송: %s → 채널 %s", message_id, channel_id)
        return {
            "message_id": message_id,
            "channel_id": channel_id,
            "sender_id": sender_id,
            "message_type": message_type,
            "status": "active",
        }

    def edit_message(
        self,
        message_id: str,
        requester_id: str,
        new_content: str,
    ) -> dict[str, Any]:
        """메시지를 수정한다.

        BR-MSG-016: 본인이 보낸 메시지만 수정 가능.

        Raises:
            ValueError: 권한 없음 또는 메시지 미존재 (ERR-MSG-016)
        """
        message = self._message_repo.find_by_id(message_id)
        if not message:
            msg = f"ERR-MSG-020: 메시지 '{message_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if message.get("sender_id") != requester_id:
            msg = "ERR-MSG-016: 본인이 보낸 메시지만 수정할 수 있습니다"
            raise ValueError(msg)

        if message.get("status") == "deleted":
            msg = "ERR-MSG-013: 삭제된 메시지는 수정할 수 없습니다"
            raise ValueError(msg)

        now = datetime.now(tz=UTC)
        self._message_repo.update_by_id(
            message_id,
            {"content": new_content, "status": "edited", "edited_at": now},
        )

        logger.info("메시지 수정: %s (요청자: %s)", message_id, requester_id)
        return {"message_id": message_id, "status": "edited"}

    def delete_message(
        self,
        message_id: str,
        requester_id: str,
    ) -> dict[str, Any]:
        """메시지를 삭제한다 (소프트 삭제).

        BR-MSG-013: 삭제된 메시지는 본문이 "(삭제된 메시지)"로 대체.
        BR-MSG-016: 본인이 보낸 메시지만 삭제 가능.

        Raises:
            ValueError: 권한 없음 또는 메시지 미존재 (ERR-MSG-016)
        """
        message = self._message_repo.find_by_id(message_id)
        if not message:
            msg = f"ERR-MSG-020: 메시지 '{message_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if message.get("sender_id") != requester_id:
            msg = "ERR-MSG-016: 본인이 보낸 메시지만 삭제할 수 있습니다"
            raise ValueError(msg)

        self._message_repo.update_by_id(
            message_id,
            {"content": _DELETED_CONTENT, "status": "deleted"},
        )

        logger.info("메시지 삭제: %s (요청자: %s)", message_id, requester_id)
        return {"message_id": message_id, "status": "deleted"}

    def add_reaction(
        self,
        message_id: str,
        user_id: str,
        emoji: str,
    ) -> dict[str, Any]:
        """메시지에 리액션을 추가한다.

        Raises:
            ValueError: 메시지 미존재 (ERR-MSG-020)
        """
        message = self._message_repo.find_by_id(message_id)
        if not message:
            msg = f"ERR-MSG-020: 메시지 '{message_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        reactions = message.get("reactions", [])
        # 동일 사용자+이모지 중복 방지
        for r in reactions:
            if r.get("user_id") == user_id and r.get("emoji") == emoji:
                return {"message_id": message_id, "already_reacted": True}

        reactions.append({"user_id": user_id, "emoji": emoji})
        self._message_repo.update_by_id(message_id, {"reactions": reactions})

        logger.info("리액션 추가: %s → 메시지 %s", emoji, message_id)
        return {"message_id": message_id, "already_reacted": False, "emoji": emoji}

    def search_messages(
        self,
        channel_id: str,
        keyword: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """채널 내 메시지를 키워드로 검색한다.

        Returns:
            검색 결과 목록
        """
        # 간단한 정규식 기반 검색
        results = self._message_repo.find_many(
            {
                "channel_id": channel_id,
                "content": {"$regex": keyword, "$options": "i"},
                "status": {"$ne": "deleted"},
            },
            limit=limit,
            sort=[("created_at", -1)],
        )

        return {"results": results, "total": len(results), "keyword": keyword}

    def create_message_from_request(self, body: Any) -> dict[str, Any]:
        """MessageCreate 요청 바디를 받아 단순 메시지를 생성한다 (Route CRUD 위임).

        비즈니스 룰 검증(채널 멤버·아카이브 등)은 send_message 에서만 적용.
        이 메서드는 route 단의 얇은 위임으로, Pydantic 레벨 검증만 신뢰.
        """
        message_id = generate_name("MSG", tenant_id=self._tenant_id)
        doc = body.model_dump()
        doc["_id"] = message_id
        doc["tenant_id"] = self._tenant_id
        self._message_repo.insert(doc)
        logger.info("메시지 생성(단순): %s", message_id)
        return {"message_id": message_id, "message": "메시지가 생성되었습니다"}

    def list_messages(
        self,
        channel_id: str | None,
        skip: int,
        limit: int,
    ) -> dict[str, Any]:
        """메시지 목록 페이지네이션."""
        query: dict[str, Any] = {}
        if channel_id:
            query["channel_id"] = channel_id
        data = self._message_repo.find_many(
            query, skip=skip, limit=limit, sort=[("created_at", -1)]
        )
        total = self._message_repo.count(query)
        return {"data": data, "total": total}

    def get_message(self, doc_id: str) -> dict[str, Any] | None:
        """메시지 상세 조회."""
        return self._message_repo.find_by_id(doc_id)

    def update_message_fields(self, doc_id: str, update_data: dict[str, Any]) -> bool:
        """메시지 수정. 존재하면 True."""
        doc = self._message_repo.find_by_id(doc_id)
        if not doc:
            return False
        self._message_repo.update_by_id(doc_id, update_data)
        return True

    def hard_delete_message(self, doc_id: str) -> bool:
        """메시지 물리 삭제. 존재하면 True."""
        doc = self._message_repo.find_by_id(doc_id)
        if not doc:
            return False
        self._message_repo.delete_by_id(doc_id)
        return True

    def _update_thread(
        self,
        channel_id: str,
        root_message_id: str,
        sender_id: str,
    ) -> None:
        """스레드 정보를 업데이트한다 (내부 메서드).

        BR-MSG-031: 스레드 참여자 목록은 자동 관리된다.
        """
        threads = self._thread_repo.find_many(
            {"root_message_id": root_message_id},
            limit=1,
        )

        now = datetime.now(tz=UTC).isoformat()

        if threads:
            thread = threads[0]
            thread_id = thread.get("_id", "")
            participants = thread.get("participants", [])
            if sender_id not in participants:
                participants.append(sender_id)
            reply_count = int(thread.get("reply_count", 0)) + 1
            self._thread_repo.update_by_id(
                thread_id,
                {
                    "participants": participants,
                    "reply_count": reply_count,
                    "last_reply_at": now,
                },
            )
        else:
            thread_id = generate_name("THR", tenant_id=self._tenant_id)
            self._thread_repo.insert(
                {
                    "_id": thread_id,
                    "channel_id": channel_id,
                    "root_message_id": root_message_id,
                    "participants": [sender_id],
                    "reply_count": 1,
                    "last_reply_at": now,
                    "tenant_id": self._tenant_id,
                }
            )
