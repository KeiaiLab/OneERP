"""재고 원장(Stock Ledger Entry) 모델 — 재고 수불부 기록."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class StockLedgerEntryCreate(BaseModel):
    """재고 원장 생성 요청 스키마."""

    item_code: str
    warehouse: str
    posting_date: date | None = None
    qty_change: Decimal = Decimal(0)
    valuation_rate: Decimal = Decimal(0)
    balance_qty: Decimal = Decimal(0)
    balance_value: Decimal = Decimal(0)
    voucher_type: str = ""
    voucher_no: str = ""
    batch_no: str | None = None


class StockLedgerEntryUpdate(BaseModel):
    """재고 원장 수정 요청 스키마."""

    item_code: str | None = None
    warehouse: str | None = None
    posting_date: date | None = None
    qty_change: Decimal | None = None
    valuation_rate: Decimal | None = None
    balance_qty: Decimal | None = None
    balance_value: Decimal | None = None
    voucher_type: str | None = None
    voucher_no: str | None = None
    batch_no: str | None = None


class StockLedgerEntry(BaseDocument):
    """재고 원장 — 품목별/창고별 재고 변동 기록.

    입고/출고/이동 시 자동 생성되는 원장 기록이다.
    재고 수량과 평가 금액을 추적한다.
    naming prefix: SLE
    """

    item_code: str = ""
    warehouse: str = ""
    posting_date: date | None = None
    qty_change: Decimal = Decimal(0)
    valuation_rate: Decimal = Decimal(0)
    balance_qty: Decimal = Decimal(0)
    balance_value: Decimal = Decimal(0)
    voucher_type: str = ""
    voucher_no: str = ""
    batch_no: str | None = None
