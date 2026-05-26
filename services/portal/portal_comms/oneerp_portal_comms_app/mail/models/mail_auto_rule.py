"""메일 자동 분류 규칙(MailAutoRule) 문서 모델.

BR-MAIL-050: 자동 규칙은 조건(condition)과 동작(action)을 반드시 포함해야 한다.
BR-MAIL-051: 규칙 우선순위(priority_order)는 양의 정수여야 한다.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class RuleConditionType(StrEnum):
    """규칙 조건 유형."""

    SENDER = "sender"
    SUBJECT_CONTAINS = "subject_contains"
    BODY_CONTAINS = "body_contains"
    HAS_ATTACHMENT = "has_attachment"
    PRIORITY = "priority"


class RuleActionType(StrEnum):
    """규칙 동작 유형."""

    MOVE_TO_FOLDER = "move_to_folder"
    ADD_TAG = "add_tag"
    MARK_AS_READ = "mark_as_read"
    STAR = "star"
    DELETE = "delete"
    FORWARD = "forward"


class RuleCondition(BaseModel):
    """자동 분류 규칙 조건."""

    condition_type: RuleConditionType
    value: str = ""


class RuleAction(BaseModel):
    """자동 분류 규칙 동작."""

    action_type: RuleActionType
    value: str = ""


class MailAutoRuleCreate(BaseModel):
    """메일 자동 분류 규칙 생성 요청 스키마."""

    rule_name: Annotated[str, Field(min_length=1, max_length=200)]
    owner_id: str = ""
    conditions: list[RuleCondition] = []
    actions: list[RuleAction] = []
    priority_order: int = 0
    is_active: bool = True
    description: str = ""

    @field_validator("conditions")
    @classmethod
    def _조건_필수(cls, v: list[RuleCondition]) -> list[RuleCondition]:
        """BR-MAIL-050: 조건은 최소 1개 이상이어야 한다."""
        if not v:
            msg = "자동 분류 규칙에는 최소 1개의 조건이 필요합니다 [ERR-MAIL-050]"
            raise ValueError(msg)
        return v

    @field_validator("actions")
    @classmethod
    def _동작_필수(cls, v: list[RuleAction]) -> list[RuleAction]:
        """BR-MAIL-050: 동작은 최소 1개 이상이어야 한다."""
        if not v:
            msg = "자동 분류 규칙에는 최소 1개의 동작이 필요합니다 [ERR-MAIL-050]"
            raise ValueError(msg)
        return v

    @field_validator("priority_order")
    @classmethod
    def _우선순위_양수(cls, v: int) -> int:
        """BR-MAIL-051: 우선순위는 양의 정수여야 한다."""
        if v < 0:
            msg = "규칙 우선순위는 0 이상이어야 합니다 [ERR-MAIL-051]"
            raise ValueError(msg)
        return v


class MailAutoRuleUpdate(BaseModel):
    """메일 자동 분류 규칙 수정 요청 스키마."""

    rule_name: str | None = None
    conditions: list[RuleCondition] | None = None
    actions: list[RuleAction] | None = None
    priority_order: int | None = None
    is_active: bool | None = None
    description: str | None = None


class MailAutoRule(BaseDocument):
    """메일 자동 분류 규칙 문서.

    BR-MAIL-050 ~ BR-MAIL-051 비즈니스 규칙을 적용한다.
    """

    rule_name: str = ""
    owner_id: str = ""
    conditions: list[RuleCondition] = []
    actions: list[RuleAction] = []
    priority_order: int = 0
    is_active: bool = True
    description: str = ""
    applied_count: int = 0
