"""알림규칙(NotificationRule) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class NotificationRuleCreate(BaseModel):
    """알림규칙 생성 요청 스키마."""

    rule_name: str
    event: str = ""
    document_type: str = ""
    condition: str = ""
    recipients: str = ""
    template: str = ""
    is_active: bool = True


class NotificationRuleUpdate(BaseModel):
    """알림규칙 수정 요청 스키마."""

    rule_name: str | None = None
    event: str | None = None
    document_type: str | None = None
    condition: str | None = None
    recipients: str | None = None
    template: str | None = None
    is_active: bool | None = None


class NotificationRule(BaseDocument):
    """알림규칙 문서 — Setup 알림규칙 설정.

    naming prefix: NTFR
    """

    rule_name: str = ""
    event: str = ""
    document_type: str = ""
    condition: str = ""
    recipients: str = ""
    template: str = ""
    is_active: bool = True
