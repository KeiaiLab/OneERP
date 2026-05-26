"""학습 인증(LearningCertification) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LearningCertificationStatus(StrEnum):
    """교육 인증 상태."""

    ACTIVE = "active"
    EXPIRED = "expired"
    RENEWED = "renewed"


class LearningCertificationCreate(BaseModel):
    """학습 인증 생성 요청 스키마."""

    employee_id: str
    certification_name: str = ""
    issuing_organization: str = ""
    issue_date: date | None = None
    expiry_date: date | None = None


class LearningCertificationUpdate(BaseModel):
    """학습 인증 수정 요청 스키마."""

    employee_id: str | None = None
    certification_name: str | None = None
    issuing_organization: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    status: LearningCertificationStatus | None = None


class LearningCertification(BaseDocument):
    """학습 인증 문서."""

    status: LearningCertificationStatus = Field(
        default=LearningCertificationStatus.ACTIVE,
        description="교육 인증 상태",
    )
    employee_id: str = ""
    certification_name: str = ""
    issuing_organization: str = ""
    issue_date: date | None = None
    expiry_date: date | None = None
