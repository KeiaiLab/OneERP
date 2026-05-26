"""위임규칙(DelegationRule) 문서 모델 — 전자결재 모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class DelegationRuleCreate(BaseModel):
    """위임규칙 생성 요청 스키마."""

    delegator: str
    delegate: str
    from_date: date | None = None
    to_date: date | None = None
    document_type: str = ""
    is_active: bool = True


class DelegationRuleUpdate(BaseModel):
    """위임규칙 수정 요청 스키마."""

    delegator: str | None = None
    delegate: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    document_type: str | None = None
    is_active: bool | None = None


class DelegationRule(BaseDocument):
    """위임규칙 문서 — 전자결재 위임 규칙 마스터.

    naming prefix: DR
    """

    delegator: str = ""
    delegate: str = ""
    from_date: date | None = None
    to_date: date | None = None
    document_type: str = ""
    is_active: bool = True


_DELEGATION_RULE_TYPES = {"date": __import__("datetime").date}

DelegationRuleCreate.model_rebuild(_types_namespace=_DELEGATION_RULE_TYPES)
DelegationRuleUpdate.model_rebuild(_types_namespace=_DELEGATION_RULE_TYPES)
DelegationRule.model_rebuild(_types_namespace=_DELEGATION_RULE_TYPES)
