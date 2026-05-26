"""시리얼/배치 번들(SerialBatchBundle) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-STK-014: 배치 유통기한 (expiry_date 검증)
- BR-STK-015: 시리얼 번호 유일성 (tenant_id + serial_no 유니크)
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SerialBatchBundleCreate(BaseModel):
    """시리얼/배치 번들 생성 요청 스키마."""

    item_code: str
    warehouse_id: str
    serial_nos: list[str] = Field(default_factory=list)
    batch_no: str = ""
    qty: Decimal = Decimal(0)


class SerialBatchBundleUpdate(BaseModel):
    """시리얼/배치 번들 수정 요청 스키마."""

    item_code: str | None = None
    warehouse_id: str | None = None
    serial_nos: list[str] | None = None
    batch_no: str | None = None
    qty: Decimal | None = None


class SerialBatchBundle(BaseDocument):
    """시리얼/배치 번들 문서."""

    item_code: str = ""
    warehouse_id: str = ""
    serial_nos: list[str] = Field(default_factory=list)
    batch_no: str = ""
    qty: Decimal = Decimal(0)
