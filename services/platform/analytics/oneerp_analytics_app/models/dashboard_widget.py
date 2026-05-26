"""대시보드 위젯(DashboardWidget) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DashboardWidgetCreate(BaseModel):
    """대시보드 위젯 생성 요청 스키마."""

    dashboard_id: str
    widget_type: str = ""
    title: str = ""
    data_source: str = ""
    position: int = 0


class DashboardWidgetUpdate(BaseModel):
    """대시보드 위젯 수정 요청 스키마."""

    dashboard_id: str | None = None
    widget_type: str | None = None
    title: str | None = None
    data_source: str | None = None
    position: int | None = None


class DashboardWidget(BaseDocument):
    """대시보드 위젯 문서."""

    dashboard_id: str = ""
    widget_type: str = ""
    title: str = ""
    data_source: str = ""
    position: int = 0
