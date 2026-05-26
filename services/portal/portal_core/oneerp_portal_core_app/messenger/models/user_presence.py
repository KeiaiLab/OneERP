"""사용자 프레즌스(UserPresence) 문서 모델.

사용자의 온라인/오프라인/부재중 상태를 관리한다.
BR-MSG-040: 프레즌스 상태는 online/offline/away/dnd 중 하나.
BR-MSG-041: 상태 메시지는 200자 이내.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class PresenceStatus(StrEnum):
    """프레즌스 상태."""

    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    DND = "dnd"


class UserPresenceCreate(BaseModel):
    """프레즌스 생성 요청 스키마.

    BR-MSG-040: 상태는 online/offline/away/dnd 중 하나.
    BR-MSG-041: 상태 메시지는 200자 이내.
    """

    user_id: str
    status: PresenceStatus = PresenceStatus.ONLINE
    status_message: str = Field("", max_length=200)


class UserPresenceUpdate(BaseModel):
    """프레즌스 수정 요청 스키마."""

    status: PresenceStatus | None = None
    status_message: str | None = Field(None, max_length=200)


class UserPresence(BaseDocument):
    """사용자 프레즌스 문서.

    BR-MSG-040, BR-MSG-041 규칙을 따른다.
    """

    user_id: str = ""
    status: PresenceStatus = PresenceStatus.OFFLINE
    status_message: str = ""
    last_seen_at: datetime | None = None
