"""위젯(Widget) 문서 모델.

포털에서 사용 가능한 위젯을 정의한다.
BR-PTL-007: 위젯 모듈 의존성 검증.
BR-PTL-008: 위젯 권한 필터링.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class WidgetType(StrEnum):
    """위젯 유형."""

    CHART = "chart"
    TABLE = "table"
    KPI = "kpi"
    LIST = "list"
    CALENDAR = "calendar"
    SHORTCUT = "shortcut"
    ANNOUNCEMENT = "announcement"
    CUSTOM = "custom"


class WidgetDataSource(BaseModel):
    """위젯 데이터 소스 설정."""

    source_type: str = Field(default="api", description="소스 유형 (api, query, static)")
    endpoint: str = Field(default="", description="API 엔드포인트")
    method: str = Field(default="GET", description="HTTP 메서드")
    params: dict[str, str] = Field(default_factory=dict, description="요청 파라미터")
    module: str = Field(default="", description="의존 모듈명")


class WidgetSize(BaseModel):
    """위젯 기본 크기."""

    min_w: int = Field(default=2, ge=1, description="최소 너비")
    min_h: int = Field(default=2, ge=1, description="최소 높이")
    default_w: int = Field(default=4, ge=1, description="기본 너비")
    default_h: int = Field(default=4, ge=1, description="기본 높이")
    max_w: int = Field(default=24, ge=1, description="최대 너비")
    max_h: int = Field(default=12, ge=1, description="최대 높이")


_WIDGET_CODE_PATTERN = re.compile(r"^WGT-[A-Z0-9_]{3,30}$")


class WidgetCreate(BaseModel):
    """위젯 생성 요청 스키마."""

    widget_code: str = Field(
        min_length=7,
        max_length=34,
        description="위젯 코드 (WGT-XXX 패턴)",
    )
    widget_name: str = Field(min_length=1, max_length=100, description="위젯 표시명")
    widget_type: WidgetType = Field(default=WidgetType.CUSTOM, description="위젯 유형")
    description: str = Field(default="", description="위젯 설명")
    data_source: WidgetDataSource = Field(
        default_factory=WidgetDataSource,
        description="데이터 소스 설정",
    )
    size: WidgetSize = Field(default_factory=WidgetSize, description="크기 설정")
    refresh_interval: Annotated[int, Field(ge=30, le=3600)] = Field(
        default=300,
        description="자동 갱신 주기 (30~3600초)",
    )
    required_permission: str = Field(default="", description="필요 권한")
    required_module: str = Field(default="", description="필요 모듈")
    is_active: bool = Field(default=True, description="활성 여부")

    @field_validator("widget_code")
    @classmethod
    def validate_widget_code(cls, v: str) -> str:
        """위젯 코드 형식 검증 (WGT-[A-Z0-9_]{3,30})."""
        if not _WIDGET_CODE_PATTERN.match(v):
            msg = f"위젯 코드 형식이 올바르지 않습니다: {v} (WGT-[A-Z0-9_] 패턴 필요)"
            raise ValueError(msg)
        return v


class WidgetUpdate(BaseModel):
    """위젯 수정 요청 스키마."""

    widget_name: str | None = None
    widget_type: WidgetType | None = None
    description: str | None = None
    data_source: WidgetDataSource | None = None
    size: WidgetSize | None = None
    refresh_interval: Annotated[int, Field(ge=30, le=3600)] | None = None
    required_permission: str | None = None
    required_module: str | None = None
    is_active: bool | None = None


class Widget(BaseDocument):
    """위젯 문서.

    BR-PTL-007: 모듈 의존성에 따라 위젯 활성화 여부 결정.
    BR-PTL-008: 권한 기반 위젯 표시 필터링.
    """

    widget_code: str = ""
    widget_name: str = ""
    widget_type: WidgetType = WidgetType.CUSTOM
    description: str = ""
    data_source: WidgetDataSource = Field(default_factory=WidgetDataSource)
    size: WidgetSize = Field(default_factory=WidgetSize)
    refresh_interval: int = 300
    required_permission: str = ""
    required_module: str = ""
    is_active: bool = True
