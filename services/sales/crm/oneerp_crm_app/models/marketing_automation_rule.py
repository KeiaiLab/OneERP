"""마케팅 자동화 규칙(MarketingAutomationRule) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class MarketingAutomationRuleCreate(BaseModel):
    """마케팅 자동화 규칙 생성 요청 스키마."""

    rule_name: str
    trigger_event: str = ""
    action: str = ""
    delay_hours: int = 0
    is_active: bool = True


class MarketingAutomationRuleUpdate(BaseModel):
    """마케팅 자동화 규칙 수정 요청 스키마."""

    rule_name: str | None = None
    trigger_event: str | None = None
    action: str | None = None
    delay_hours: int | None = None
    is_active: bool | None = None


class MarketingAutomationRule(BaseDocument):
    """마케팅 자동화 규칙 문서."""

    rule_name: str = ""
    trigger_event: str = ""
    action: str = ""
    delay_hours: int = 0
    is_active: bool = True
