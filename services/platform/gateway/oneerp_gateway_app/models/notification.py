"""알림 템플릿(NotificationTemplate) 모델 정의."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class NotificationEvent(StrEnum):
    """알림 트리거 이벤트."""

    ON_CREATE = "on_create"
    ON_UPDATE = "on_update"
    ON_SUBMIT = "on_submit"
    ON_CANCEL = "on_cancel"


class NotificationChannel(StrEnum):
    """알림 채널."""

    EMAIL = "email"
    SYSTEM = "system"
    SMS = "sms"


class NotificationTemplate(BaseDocument):
    """알림 템플릿 문서 — 이벤트 기반 알림 설정.

    naming prefix: NOTIF
    """

    name: str = ""
    document_type: str = ""
    event: NotificationEvent = NotificationEvent.ON_CREATE
    channel: NotificationChannel = NotificationChannel.SYSTEM
    subject_template: str = ""
    message_template: str = ""
    recipients_expression: str = ""


class NotificationTemplateCreate(BaseModel):
    """알림 템플릿 생성 요청 스키마."""

    name: str
    document_type: str
    event: NotificationEvent = NotificationEvent.ON_CREATE
    channel: NotificationChannel = NotificationChannel.SYSTEM
    subject_template: str = ""
    message_template: str = ""
    recipients_expression: str = ""


class NotificationTemplateUpdate(BaseModel):
    """알림 템플릿 수정 요청 스키마 — 모든 필드 선택적."""

    name: str | None = None
    document_type: str | None = None
    event: NotificationEvent | None = None
    channel: NotificationChannel | None = None
    subject_template: str | None = None
    message_template: str | None = None
    recipients_expression: str | None = None
