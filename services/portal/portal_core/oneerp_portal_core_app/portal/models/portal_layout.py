"""포털 레이아웃(PortalLayout) 문서 모델.

레이아웃 상속 계층: 글로벌 → 부서 → 역할 → 개인.
BR-PTL-001: 4단계 레이아웃 상속 체계.
BR-PTL-002: 위젯 최대 50개 제한.
BR-PTL-010: 레이아웃 잠금 시 수정 불가.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class LayoutScope(StrEnum):
    """레이아웃 적용 범위."""

    GLOBAL = "global"
    DEPARTMENT = "department"
    ROLE = "role"
    PERSONAL = "personal"


class WidgetPlacement(BaseModel):
    """위젯 배치 정보 — 그리드 내 위치와 크기."""

    widget_id: str = Field(description="위젯 ID 참조")
    grid_x: int = Field(default=0, ge=0, description="그리드 X 좌표")
    grid_y: int = Field(default=0, ge=0, description="그리드 Y 좌표")
    grid_w: int = Field(default=4, ge=1, le=24, description="그리드 너비 (1~24)")
    grid_h: int = Field(default=4, ge=1, description="그리드 높이")
    is_visible: bool = Field(default=True, description="표시 여부")


class ThemeConfig(BaseModel):
    """테마 설정."""

    primary_color: str = Field(default="#1976D2", description="주 색상")
    background_color: str = Field(default="#FFFFFF", description="배경 색상")
    font_family: str = Field(default="Pretendard", description="폰트 패밀리")
    dark_mode: bool = Field(default=False, description="다크 모드 여부")


class MobileLayoutConfig(BaseModel):
    """모바일 레이아웃 설정.

    BR-PTL-013: 모바일 자동 리플로우 설정.
    """

    columns: int = Field(default=1, ge=1, le=4, description="모바일 컬럼 수")
    stack_order: list[str] = Field(
        default_factory=list,
        description="위젯 스택 순서 (widget_id 목록)",
    )
    hide_widgets: list[str] = Field(
        default_factory=list,
        description="모바일에서 숨길 위젯 ID 목록",
    )


class PortalLayoutCreate(BaseModel):
    """포털 레이아웃 생성 요청 스키마."""

    layout_name: str = Field(min_length=1, max_length=100, description="레이아웃 이름")
    scope: LayoutScope = Field(default=LayoutScope.GLOBAL, description="적용 범위")
    scope_value: str = Field(default="", description="범위 값 (부서 ID, 역할명 등)")
    grid_columns: Annotated[int, Field(ge=1, le=24)] = Field(
        default=12,
        description="그리드 컬럼 수 (1~24)",
    )
    grid_row_height: Annotated[int, Field(ge=40, le=200)] = Field(
        default=80,
        description="그리드 행 높이 (40~200px)",
    )
    widgets: list[WidgetPlacement] = Field(default_factory=list, description="위젯 배치 목록")
    theme: ThemeConfig = Field(default_factory=ThemeConfig, description="테마 설정")
    mobile_config: MobileLayoutConfig = Field(
        default_factory=MobileLayoutConfig,
        description="모바일 레이아웃 설정",
    )
    is_locked: bool = Field(default=False, description="레이아웃 잠금 여부")
    parent_layout_id: str = Field(default="", description="상위 레이아웃 ID (상속)")

    @field_validator("widgets")
    @classmethod
    def validate_max_widgets(cls, v: list[WidgetPlacement]) -> list[WidgetPlacement]:
        """BR-PTL-002: 위젯 최대 50개 제한 검증."""
        max_widgets = 50
        if len(v) > max_widgets:
            msg = f"위젯은 최대 {max_widgets}개까지 배치할 수 있습니다 (현재: {len(v)}개)"
            raise ValueError(msg)
        return v


class PortalLayoutUpdate(BaseModel):
    """포털 레이아웃 수정 요청 스키마."""

    layout_name: str | None = None
    scope: LayoutScope | None = None
    scope_value: str | None = None
    grid_columns: Annotated[int, Field(ge=1, le=24)] | None = None
    grid_row_height: Annotated[int, Field(ge=40, le=200)] | None = None
    widgets: list[WidgetPlacement] | None = None
    theme: ThemeConfig | None = None
    mobile_config: MobileLayoutConfig | None = None
    is_locked: bool | None = None
    parent_layout_id: str | None = None

    @field_validator("widgets")
    @classmethod
    def validate_max_widgets(cls, v: list[WidgetPlacement] | None) -> list[WidgetPlacement] | None:
        """BR-PTL-002: 위젯 최대 50개 제한 검증."""
        max_widgets = 50
        if v is not None and len(v) > max_widgets:
            msg = f"위젯은 최대 {max_widgets}개까지 배치할 수 있습니다 (현재: {len(v)}개)"
            raise ValueError(msg)
        return v


class PortalLayout(BaseDocument):
    """포털 레이아웃 문서.

    BR-PTL-001: 4단계 상속 (글로벌→부서→역할→개인).
    BR-PTL-002: 최대 50개 위젯.
    BR-PTL-010: 잠금 시 수정 불가.
    """

    layout_name: str = ""
    scope: LayoutScope = LayoutScope.GLOBAL
    scope_value: str = ""
    grid_columns: int = 12
    grid_row_height: int = 80
    widgets: list[WidgetPlacement] = Field(default_factory=list)
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
    mobile_config: MobileLayoutConfig = Field(default_factory=MobileLayoutConfig)
    is_locked: bool = False
    parent_layout_id: str = ""
