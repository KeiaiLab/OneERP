"""교대 유형(ShiftType) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ShiftTypeCreate(BaseModel):
    """교대 유형 생성 요청 스키마."""

    shift_name: str
    start_time: str = ""
    end_time: str = ""
    working_hours: Decimal = Decimal(0)


class ShiftTypeUpdate(BaseModel):
    """교대 유형 수정 요청 스키마."""

    shift_name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    working_hours: Decimal | None = None


class ShiftType(BaseDocument):
    """교대 유형 문서."""

    shift_name: str = ""
    start_time: str = ""
    end_time: str = ""
    working_hours: Decimal = Decimal(0)
