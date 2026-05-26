"""공급업체견적(Supplier Quotation) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class SupplierQuotationItem(LineItem):
    """공급업체견적 라인 아이템."""

    item_code: str
    item_name: str
    qty: Decimal
    rate: Decimal
    amount: Decimal = Decimal(0)


class SupplierQuotationCreate(BaseModel):
    """공급업체견적 생성 요청 스키마."""

    rfq_reference: str = ""
    supplier: str = ""
    supplier_name: str = ""
    transaction_date: date | None = None
    valid_till: date | None = None
    items: list[SupplierQuotationItem] = []


class SupplierQuotationUpdate(BaseModel):
    """공급업체견적 수정 요청 스키마."""

    rfq_reference: str | None = None
    supplier: str | None = None
    supplier_name: str | None = None
    transaction_date: date | None = None
    valid_till: date | None = None
    items: list[SupplierQuotationItem] | None = None


class SupplierQuotation(BaseDocument):
    """공급업체견적 문서 — 공급업체로부터 받은 견적서.

    naming prefix: SQ
    """

    rfq_reference: str = ""
    supplier: str = ""
    supplier_name: str = ""  # 비정규화
    transaction_date: date | None = None
    valid_till: date | None = None
    items: list[SupplierQuotationItem] = []
    total: Decimal = Decimal(0)
    grand_total: Decimal = Decimal(0)
