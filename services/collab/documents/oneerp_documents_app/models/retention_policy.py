"""보존 정책(RetentionPolicy) 모델 — 문서 보존 기간과 만료 처리 방법 정의.

BR-DOC-003: 보존 정책 자동 적용.
BR-DOC-011: 보존 기간 내 삭제 금지.
BR-DOC-012: 폐기 결재 필수.
"""

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

    policy_name: str = Field(min_length=1, max_length=200, description="정책명")
    description: str = Field(default="", description="설명")
    retention_years: int = Field(ge=1, le=100, description="보존 기간 (년)")
    retention_months: int = Field(default=0, ge=0, le=11, description="보존 기간 (추가 월)")
    action_on_expiry: ExpiryAction = Field(default=ExpiryAction.REVIEW, description="만료 시 처리")
    requires_approval: bool = Field(default=True, description="폐기 시 결재 필요")
    legal_basis: str = Field(default="", description="법적 근거")


class RetentionPolicyUpdate(BaseModel):
    """보존 정책 수정 요청 스키마."""

    policy_name: str | None = None
    description: str | None = None
    retention_years: int | None = None
    retention_months: int | None = None
    action_on_expiry: ExpiryAction | None = None
    requires_approval: bool | None = None
    legal_basis: str | None = None
    is_active: bool | None = None


class RetentionPolicy(BaseDocument):
    """보존 정책 엔티티.

    문서 보존 기간과 만료 시 처리 방법을 정의하는 마스터 데이터.
    """

    policy_name: str = ""
    description: str = ""
    retention_years: int = 1
    retention_months: int = 0
    action_on_expiry: ExpiryAction = ExpiryAction.REVIEW
    requires_approval: bool = True
    legal_basis: str = ""
    is_system: bool = False
    is_active: bool = True
