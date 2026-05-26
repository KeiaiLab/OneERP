"""시리얼번호(SerialNo) 모델 정의."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SerialNo(BaseDocument):
    """시리얼번호 마스터 — 개별 추적 관리.

    naming prefix: SN
    """

    serial_no: str = ""
    item_code: str = ""
    item_name: str = ""
    status: str = "active"
    warehouse: str = ""
    purchase_date: date | None = None
    delivery_date: date | None = None


class SerialNoCreate(BaseModel):
    """시리얼번호 생성 요청."""

    serial_no: str = ""
    item_code: str = ""
    item_name: str = ""
    status: str = "active"
    warehouse: str = ""
    purchase_date: date | None = None
    delivery_date: date | None = None


class SerialNoUpdate(BaseModel):
    """시리얼번호 수정 요청."""

    serial_no: str | None = None
    item_code: str | None = None
    item_name: str | None = None
    status: str | None = None
    warehouse: str | None = None
    purchase_date: date | None = None
    delivery_date: date | None = None
