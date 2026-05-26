"""작업장(Workstation) 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class Workstation(BaseDocument):
    """작업장 마스터 — 생산 설비 정보.

    naming prefix: WS
    """

    workstation_name: str = ""
    production_capacity: int = 1
    hourly_rate: Decimal = Decimal(0)
    is_active: bool = True


class WorkstationCreate(BaseModel):
    """작업장 생성 요청."""

    workstation_name: str = ""
    production_capacity: int = 1
    hourly_rate: Decimal = Decimal(0)
    is_active: bool = True


class WorkstationUpdate(BaseModel):
    """작업장 수정 요청."""

    workstation_name: str | None = None
    production_capacity: int | None = None
    hourly_rate: Decimal | None = None
    is_active: bool | None = None
