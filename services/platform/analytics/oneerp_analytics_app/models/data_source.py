"""데이터 소스(DataSource) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DataSourceStatus(StrEnum):
    """데이터 소스 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class DataSourceCreate(BaseModel):
    """데이터 소스 생성 요청 스키마."""

    source_name: str
    source_type: str = ""
    connection_info: str = ""
    is_active: bool = True


class DataSourceUpdate(BaseModel):
    """데이터 소스 수정 요청 스키마."""

    source_name: str | None = None
    source_type: str | None = None
    connection_info: str | None = None
    is_active: bool | None = None


class DataSource(BaseDocument):
    """데이터 소스 문서."""

    status: DataSourceStatus = Field(
        default=DataSourceStatus.ACTIVE,
        description="데이터 소스 상태",
    )
    source_name: str = ""
    source_type: str = ""
    connection_info: str = ""
    is_active: bool = True
