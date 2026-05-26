"""국세청 연동(NTSIntegration) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class NTSIntegrationStatus(StrEnum):
    """국세청 연동 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class NTSIntegrationCreate(BaseModel):
    """국세청 연동 생성 요청 스키마."""

    integration_type: str
    cert_path: str = ""
    business_no: str = ""
    is_active: bool = True


class NTSIntegrationUpdate(BaseModel):
    """국세청 연동 수정 요청 스키마."""

    integration_type: str | None = None
    cert_path: str | None = None
    business_no: str | None = None
    is_active: bool | None = None


class NTSIntegration(BaseDocument):
    """국세청 연동 문서."""

    status: NTSIntegrationStatus = Field(
        default=NTSIntegrationStatus.ACTIVE,
        description="국세청 연동 상태",
    )
    integration_type: str = ""
    cert_path: str = ""
    business_no: str = ""
    is_active: bool = True
