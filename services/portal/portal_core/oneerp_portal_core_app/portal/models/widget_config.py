"""위젯 설정(WidgetConfig) 문서 모델.

사용자별 위젯 커스텀 설정을 저장한다.
"""

from __future__ import annotations

from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WidgetConfigCreate(BaseModel):
    """위젯 설정 생성 요청 스키마."""

    widget_id: str = Field(description="위젯 ID")
    user_id: str = Field(description="사용자 ID")
    config_data: dict[str, Any] = Field(default_factory=dict, description="커스텀 설정 데이터")
    is_collapsed: bool = Field(default=False, description="접힘 여부")
    custom_title: str = Field(default="", description="커스텀 제목")


class WidgetConfigUpdate(BaseModel):
    """위젯 설정 수정 요청 스키마."""

    config_data: dict[str, Any] | None = None
    is_collapsed: bool | None = None
    custom_title: str | None = None


class WidgetConfig(BaseDocument):
    """위젯 설정 문서.

    사용자별로 위젯의 개인화 설정을 관리한다.
    """

    widget_id: str = ""
    user_id: str = ""
    config_data: dict[str, Any] = Field(default_factory=dict)
    is_collapsed: bool = False
    custom_title: str = ""
