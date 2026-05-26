"""유지보수 요청(MaintenanceRequest) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class MaintenanceRequestCreate(BaseModel):
    """유지보수 요청 생성 요청 스키마."""

    asset_id: str
    request_date: date | None = None
    description: str = ""
    priority: str = ""
    requested_by: str = ""
    is_resolved: bool = False


class MaintenanceRequestUpdate(BaseModel):
    """유지보수 요청 수정 요청 스키마."""

    asset_id: str | None = None
    request_date: date | None = None
    description: str | None = None
    priority: str | None = None
    requested_by: str | None = None
    is_resolved: bool | None = None


class MaintenanceRequest(BaseDocument):
    """유지보수 요청 문서."""

    asset_id: str = ""
    request_date: date | None = None
    description: str = ""
    priority: str = ""
    requested_by: str = ""
    is_resolved: bool = False
