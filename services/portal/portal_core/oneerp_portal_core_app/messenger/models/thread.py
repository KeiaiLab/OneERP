"""스레드(Thread) 문서 모델.

메시지 스레드(답글 그룹)를 관리한다.
BR-MSG-030: 스레드의 root_message_id는 필수이며 존재하는 메시지여야 한다.
BR-MSG-031: 스레드 참여자 목록은 자동 관리된다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ThreadCreate(BaseModel):
    """스레드 생성 요청 스키마.

    BR-MSG-030: root_message_id는 필수.
    """

    channel_id: str
    root_message_id: str
    participants: list[str] = Field(default_factory=list)


class ThreadUpdate(BaseModel):
    """스레드 수정 요청 스키마."""

    participants: list[str] | None = None


class Thread(BaseDocument):
    """스레드 문서.

    BR-MSG-030, BR-MSG-031 규칙을 따른다.
    """

    channel_id: str = ""
    root_message_id: str = ""
    participants: list[str] = Field(default_factory=list)
    reply_count: int = 0
    last_reply_at: str | None = None
