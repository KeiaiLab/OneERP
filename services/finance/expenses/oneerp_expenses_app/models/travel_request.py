"""출장신청(TravelRequest) 문서 모델 — Expenses 모듈.

L2 비즈니스 룰: BR-EXP-011 (출장 기간 검증 start_date <= end_date).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from datetime import date


class TravelRequestCreate(BaseModel):
    """출장신청 생성 요청 스키마."""

    employee_id: str
    purpose: str = ""
    departure_date: date | None = None
    return_date: date | None = None
    destination: str = ""
    estimated_cost: Decimal = Decimal(0)

    @model_validator(mode="after")
    def _출발일은_귀환일_이전(self) -> TravelRequestCreate:
        """BR-EXP-011: 출발일 <= 귀환일 검증."""
        if (
            self.departure_date is not None
            and self.return_date is not None
            and self.departure_date > self.return_date
        ):
            raise ValueError("출발일은 귀환일 이전이어야 합니다")
        return self


class TravelRequestUpdate(BaseModel):
    """출장신청 수정 요청 스키마."""

    employee_id: str | None = None
    purpose: str | None = None
    departure_date: date | None = None
    return_date: date | None = None
    destination: str | None = None
    estimated_cost: Decimal | None = None


class TravelRequest(BaseDocument):
    """출장신청 문서 — Expenses 출장 트랜잭션.

    naming prefix: TR
    """

    employee_id: str = Field(default="", alias="employee")
    purpose: str = ""
    departure_date: date | None = None
    return_date: date | None = None
    destination: str = ""
    estimated_cost: Decimal = Decimal(0)
