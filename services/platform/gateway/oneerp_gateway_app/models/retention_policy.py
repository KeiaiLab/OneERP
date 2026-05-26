"""보존 정책(RetentionPolicy) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ExpiryAction(StrEnum):
    """만료 시 처리 방법."""

    ARCHIVE = "archive"
    DELETE = "delete"
    REVIEW = "review"


class RetentionPolicyCreate(BaseModel):
    """보존 정책 생성 요청 스키마."""

    policy_name: str = Field(min_length=1, max_length=200)
    description: str = ""
    retention_years: int = Field(default=5, ge=1, le=100)
    retention_months: int = Field(default=0, ge=0, le=11)
    action_on_expiry: ExpiryAction = ExpiryAction.REVIEW
    requires_approval: bool = True
    legal_basis: str = ""
    is_system: bool = False
    is_active: bool = True


class RetentionPolicyUpdate(BaseModel):
    """보존 정책 수정 요청 스키마."""

    policy_name: str | None = None
    retention_years: int | None = None
    description: str | None = None
    retention_months: int | None = None
    action_on_expiry: ExpiryAction | None = None
    requires_approval: bool | None = None
    legal_basis: str | None = None
    is_system: bool | None = None
    is_active: bool | None = None


class RetentionPolicy(BaseDocument):
    """보존 정책 문서."""

    policy_name: str = ""
    description: str = ""
    retention_years: int = 5
    retention_months: int = 0
    action_on_expiry: ExpiryAction = ExpiryAction.REVIEW
    requires_approval: bool = True
    legal_basis: str = ""
    is_system: bool = False
    is_active: bool = True
