"""캘린더(Calendar) 문서 모델.

BR-CAL-001: 캘린더는 고유한 이름을 가져야 한다.
BR-CAL-002: 캘린더는 소유자가 반드시 지정되어야 한다.
BR-CAL-003: 공개/비공개/팀 가시성을 설정할 수 있다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator


class CalendarVisibility(StrEnum):
    """캘린더 가시성."""

    PRIVATE = "private"
    PUBLIC = "public"
    TEAM = "team"


class CalendarStatus(StrEnum):
    """캘린더 상태."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class CalendarCreate(BaseModel):
    """캘린더 생성 요청 스키마."""

    name: str
    description: str = ""
    owner_id: str
    visibility: CalendarVisibility = CalendarVisibility.PRIVATE
    color: str = "#1a73e8"
    timezone: str = "Asia/Seoul"
    team_id: str = ""

    @model_validator(mode="after")
    def _validate_team_visibility(self) -> CalendarCreate:
        """BR-CAL-003: 팀 캘린더는 team_id가 필수."""
        if self.visibility == CalendarVisibility.TEAM and not self.team_id:
            msg = "팀 캘린더는 team_id가 필수입니다 (ERR-CAL-001)"
            raise ValueError(msg)
        return self


class CalendarUpdate(BaseModel):
    """캘린더 수정 요청 스키마."""

    name: str | None = None
    description: str | None = None
    visibility: CalendarVisibility | None = None
    color: str | None = None
    timezone: str | None = None
    status: CalendarStatus | None = None
    team_id: str | None = None


class Calendar(BaseDocument):
    """캘린더 문서 — 일정 컨테이너.

    naming prefix: CAL
    BR-CAL-001: 캘린더는 고유한 이름을 가져야 한다.
    BR-CAL-002: 캘린더는 소유자가 반드시 지정되어야 한다.
    """

    name: str = Field(default="", description="캘린더 이름")
    description: str = Field(default="", description="설명")
    owner_id: str = Field(default="", description="소유자 ID")
    visibility: CalendarVisibility = Field(
        default=CalendarVisibility.PRIVATE,
        description="가시성",
    )
    color: str = Field(default="#1a73e8", description="표시 색상")
    timezone: str = Field(default="Asia/Seoul", description="기본 시간대")
    status: CalendarStatus = Field(default=CalendarStatus.ACTIVE, description="캘린더 상태")
    team_id: str = Field(default="", description="팀 ID (팀 캘린더)")
