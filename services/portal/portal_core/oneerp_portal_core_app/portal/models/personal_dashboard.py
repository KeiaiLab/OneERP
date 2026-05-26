"""개인 대시보드(PersonalDashboard) 문서 모델.

사용자별 대시보드 설정 및 위젯 배치를 관리한다.
"""

from __future__ import annotations

from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

from .portal_layout import WidgetPlacement  # noqa: TC001


class PersonalDashboardCreate(BaseModel):
    """개인 대시보드 생성 요청 스키마."""

    user_id: str = Field(default="", description="사용자 ID (서버에서 설정)")
    dashboard_name: str = Field(
        default="내 대시보드",
        max_length=100,
        description="대시보드 이름",
    )
    widgets: list[WidgetPlacement] = Field(
        default_factory=list,
        description="위젯 배치 목록",
    )
    preferences: dict[str, Any] = Field(default_factory=dict, description="개인 설정")


class PersonalDashboardUpdate(BaseModel):
    """개인 대시보드 수정 요청 스키마."""

    dashboard_name: str | None = None
    widgets: list[WidgetPlacement] | None = None
    preferences: dict[str, Any] | None = None


class PersonalDashboard(BaseDocument):
    """개인 대시보드 문서."""

    user_id: str = ""
    dashboard_name: str = "내 대시보드"
    widgets: list[WidgetPlacement] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)
    base_layout_id: str = ""
