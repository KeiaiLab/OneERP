"""보험 연동(InsuranceIntegration) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class InsuranceIntegrationStatus(StrEnum):
    """보험 연동 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class InsuranceIntegrationCreate(BaseModel):
    """보험 연동 생성 요청 스키마."""

    insurance_type: str
    provider: str = ""
    account_id: str = ""
    is_active: bool = True


class InsuranceIntegrationUpdate(BaseModel):
    """보험 연동 수정 요청 스키마."""

    insurance_type: str | None = None
    provider: str | None = None
    account_id: str | None = None
    is_active: bool | None = None


class InsuranceIntegration(BaseDocument):
    """보험 연동 문서."""

    status: InsuranceIntegrationStatus = Field(
        default=InsuranceIntegrationStatus.ACTIVE,
        description="보험 연동 상태",
    )
    insurance_type: str = ""
    provider: str = ""
    account_id: str = ""
    is_active: bool = True
