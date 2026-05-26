"""직위/보직(Position) 마스터 모델 — 조직도/인명부 모듈.

BR-DIR-006: 직위는 조직 단위(org_unit_id)에 귀속된다.
BR-DIR-007: 직위별 정원(headcount)을 관리한다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class PositionStatus(StrEnum):
    """직위 상태."""

    OPEN = "open"  # 공석
    FILLED = "filled"  # 충원됨
    FROZEN = "frozen"  # 동결


class PositionCreate(BaseModel):
    """직위 생성 요청 스키마.

    BR-DIR-006: org_unit_id는 필수이다.
    """

    org_unit_id: str
    position_code: str
    position_title: str
    position_title_en: str = ""
    grade: str = ""
    headcount: int = 1
    job_description: str = ""

    @field_validator("org_unit_id")
    @classmethod
    def org_unit_required(cls, v: str) -> str:
        """BR-DIR-006: 소속 조직 단위는 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-006: 소속 조직 단위 ID는 필수입니다"
            raise ValueError(msg)
        return v.strip()

    @field_validator("position_code")
    @classmethod
    def position_code_required(cls, v: str) -> str:
        """직위 코드는 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-007: 직위 코드는 필수입니다"
            raise ValueError(msg)
        return v.strip()

    @field_validator("headcount")
    @classmethod
    def headcount_positive(cls, v: int) -> int:
        """BR-DIR-007: 정원은 1 이상이어야 한다."""
        if v < 1:
            msg = "ERR-DIR-008: 정원은 1 이상이어야 합니다"
            raise ValueError(msg)
        return v


class PositionUpdate(BaseModel):
    """직위 수정 요청 스키마."""

    position_code: str | None = None
    position_title: str | None = None
    position_title_en: str | None = None
    grade: str | None = None
    headcount: int | None = None
    job_description: str | None = None
    status: PositionStatus | None = None


class Position(BaseDocument):
    """직위/보직 마스터 — 조직 단위 내 직위 정의.

    naming prefix: POS
    BR-DIR-006, BR-DIR-007
    """

    org_unit_id: str = Field(default="", description="소속 조직 단위 ID")
    position_code: str = Field(default="", description="직위 코드")
    position_title: str = Field(default="", description="직위명")
    position_title_en: str = Field(default="", description="직위 영문명")
    grade: str = Field(default="", description="직급")
    headcount: int = Field(default=1, description="정원")
    filled_count: int = Field(default=0, description="현 충원 인원")
    job_description: str = Field(default="", description="직무 기술서")
    status: PositionStatus = Field(default=PositionStatus.OPEN, description="상태")
