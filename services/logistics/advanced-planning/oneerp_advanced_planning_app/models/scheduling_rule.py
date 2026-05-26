"""스케줄링 규칙 모델 — 생산 스케줄 최적화 규칙을 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SchedulingRuleCreate(BaseModel):
    """스케줄링 규칙 생성 요청 스키마."""

    rule_name: str
    rule_type: str = "priority"  # priority/fifo/edd/spt/critical_ratio
    priority: int = 0
    conditions: dict = {}
    parameters: dict = {}
    description: str = ""


class SchedulingRuleUpdate(BaseModel):
    """스케줄링 규칙 수정 요청 스키마."""

    rule_name: str | None = None
    priority: int | None = None
    conditions: dict | None = None
    parameters: dict | None = None
    is_active: bool | None = None
    description: str | None = None


class SchedulingRule(BaseDocument):
    """스케줄링 규칙 문서 — 생산 스케줄 최적화 규칙을 저장한다."""

    rule_name: str = ""
    rule_type: str = "priority"
    priority: int = 0
    conditions: dict = {}
    parameters: dict = {}
    description: str = ""
    is_active: bool = True
