"""알림(Notification) 문서 모델.

사내 메신저의 알림을 정의한다.
BR-MSG-020: 알림 유형은 mention/reply/channel_invite/system 중 하나.
BR-MSG-021: 읽음 처리된 알림은 다시 미읽음으로 변경 불가.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class NotificationType(StrEnum):
    """알림 유형."""

    MENTION = "mention"
    REPLY = "reply"
    CHANNEL_INVITE = "channel_invite"
    SYSTEM = "system"


class NotificationCreate(BaseModel):
    """알림 생성 요청 스키마.

    BR-MSG-020: 알림 유형은 mention/reply/channel_invite/system 중 하나.
    """

    user_id: str
    notification_type: NotificationType
    title: str = ""
    body: str = ""
    reference_id: str = ""
    channel_id: str = ""


class NotificationUpdate(BaseModel):
    """알림 수정 요청 스키마."""

    is_read: bool | None = None


class Notification(BaseDocument):
    """알림 문서.

    BR-MSG-020, BR-MSG-021 규칙을 따른다.
    """

    user_id: str = ""
    notification_type: NotificationType = NotificationType.SYSTEM
    title: str = ""
    body: str = ""
    reference_id: str = ""
    channel_id: str = ""
    is_read: bool = False
