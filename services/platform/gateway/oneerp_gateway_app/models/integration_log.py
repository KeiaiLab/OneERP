"""연동 로그(IntegrationLog) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class IntegrationLogCreate(BaseModel):
    """연동 로그 생성 요청 스키마."""

    connector_id: str
    direction: str = ""
    request_data: str = ""
    response_data: str = ""
    is_success: bool = True
    error_message: str = ""


class IntegrationLogUpdate(BaseModel):
    """연동 로그 수정 요청 스키마."""

    connector_id: str | None = None
    direction: str | None = None
    request_data: str | None = None
    response_data: str | None = None
    is_success: bool | None = None
    error_message: str | None = None


class IntegrationLog(BaseDocument):
    """연동 로그 문서."""

    connector_id: str = ""
    direction: str = ""
    request_data: str = ""
    response_data: str = ""
    is_success: bool = True
    error_message: str = ""
