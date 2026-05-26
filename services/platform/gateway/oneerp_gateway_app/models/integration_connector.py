"""연동 커넥터(IntegrationConnector) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class IntegrationConnectorStatus(StrEnum):
    """연동 커넥터 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class IntegrationConnectorCreate(BaseModel):
    """연동 커넥터 생성 요청 스키마."""

    connector_name: str
    connector_type: str = ""
    base_url: str = ""
    auth_type: str = ""
    is_active: bool = True


class IntegrationConnectorUpdate(BaseModel):
    """연동 커넥터 수정 요청 스키마."""

    connector_name: str | None = None
    connector_type: str | None = None
    base_url: str | None = None
    auth_type: str | None = None
    is_active: bool | None = None


class IntegrationConnector(BaseDocument):
    """연동 커넥터 문서."""

    status: IntegrationConnectorStatus = Field(
        default=IntegrationConnectorStatus.ACTIVE,
        description="연동 커넥터 상태",
    )
    connector_name: str = ""
    connector_type: str = ""
    base_url: str = ""
    auth_type: str = ""
    is_active: bool = True
