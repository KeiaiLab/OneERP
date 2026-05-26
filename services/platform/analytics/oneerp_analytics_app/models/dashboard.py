"""대시보드(Dashboard) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DashboardCreate(BaseModel):
    """대시보드 생성 요청 스키마."""

    dashboard_name: str
    description: str = ""
    is_public: bool = False
    owner: str = ""


class DashboardUpdate(BaseModel):
    """대시보드 수정 요청 스키마."""

    dashboard_name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    owner: str | None = None


class Dashboard(BaseDocument):
    """대시보드 문서."""

    dashboard_name: str = ""
    description: str = ""
    is_public: bool = False
    owner: str = ""
