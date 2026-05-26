"""공정(Operation) 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class Operation(BaseDocument):
    """공정 마스터 — 생산 공정 정의.

    naming prefix: OPR
    """

    operation_name: str = ""
    workstation: str = ""
    time_in_mins: Decimal = Decimal(0)
    description: str = ""
    is_active: bool = True


class OperationCreate(BaseModel):
    """공정 생성 요청."""

    operation_name: str = ""
    workstation: str = ""
    time_in_mins: Decimal = Decimal(0)
    description: str = ""
    is_active: bool = True


class OperationUpdate(BaseModel):
    """공정 수정 요청."""

    operation_name: str | None = None
    workstation: str | None = None
    time_in_mins: Decimal | None = None
    description: str | None = None
    is_active: bool | None = None
