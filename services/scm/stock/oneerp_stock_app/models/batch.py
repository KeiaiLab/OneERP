"""로트(Batch) 모델 — 품목의 생산/유통 추적 단위."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class Batch(BaseDocument):
    """로트(배치) — 품목의 생산 로트 추적.

    naming prefix: BATCH
    """

    batch_id: str = ""
    item_code: str = ""
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    supplier_ref: str | None = None
    status: str = "active"


class BatchCreate(BaseModel):
    """로트 생성 요청."""

    item_code: str
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    supplier_ref: str | None = None


class BatchUpdate(BaseModel):
    """로트 수정 요청."""

    manufacturing_date: date | None = None
    expiry_date: date | None = None
    supplier_ref: str | None = None
    status: str | None = None
