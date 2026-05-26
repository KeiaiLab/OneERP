"""공정 손실(ProcessLoss) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ProcessLossCreate(BaseModel):
    """공정 손실 생성 요청 스키마."""

    work_order_id: str
    item_code: str = ""
    expected_qty: Decimal = Decimal(0)
    actual_qty: Decimal = Decimal(0)
    loss_qty: Decimal = Decimal(0)
    loss_percentage: Decimal = Decimal(0)


class ProcessLossUpdate(BaseModel):
    """공정 손실 수정 요청 스키마."""

    work_order_id: str | None = None
    item_code: str | None = None
    expected_qty: Decimal | None = None
    actual_qty: Decimal | None = None
    loss_qty: Decimal | None = None
    loss_percentage: Decimal | None = None


class ProcessLoss(BaseDocument):
    """공정 손실 문서."""

    work_order_id: str = ""
    item_code: str = ""
    expected_qty: Decimal = Decimal(0)
    actual_qty: Decimal = Decimal(0)
    loss_qty: Decimal = Decimal(0)
    loss_percentage: Decimal = Decimal(0)
