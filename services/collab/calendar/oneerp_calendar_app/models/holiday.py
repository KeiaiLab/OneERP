"""공휴일(Holiday) 문서 모델.

BR-CAL-060: 공휴일은 날짜와 이름이 필수이다.
BR-CAL-061: 동일 날짜에 중복 공휴일 등록 불가.
BR-CAL-062: 공휴일은 연간 반복 설정이 가능하다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class HolidayCreate(BaseModel):
    """공휴일 생성 요청 스키마."""

    name: str
    holiday_date: date
    description: str = ""
    is_annual: bool = True
    country: str = "KR"


class HolidayUpdate(BaseModel):
    """공휴일 수정 요청 스키마."""

    name: str | None = None
    holiday_date: date | None = None
    description: str | None = None
    is_annual: bool | None = None
    country: str | None = None


class Holiday(BaseDocument):
    """공휴일 문서.

    naming prefix: CHOL
    BR-CAL-060: 공휴일은 날짜와 이름이 필수이다.
    BR-CAL-062: 공휴일은 연간 반복 설정이 가능하다.
    """

    name: str = Field(default="", description="공휴일 이름")
    holiday_date: date | None = Field(default=None, description="공휴일 날짜")
    description: str = Field(default="", description="설명")
    is_annual: bool = Field(default=True, description="매년 반복 여부")
    country: str = Field(default="KR", description="국가 코드")
