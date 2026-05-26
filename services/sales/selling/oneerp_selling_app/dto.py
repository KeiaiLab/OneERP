"""selling 서비스의 Create/Update/Request/Response DTO 집약.

OE004: models/는 Document(영속 상태)만, dto는 여기에 모은다.
"""

from __future__ import annotations

from datetime import date  # noqa: TC003
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .models.delivery_note import DeliveryNoteItem
    from .models.sales_invoice import SalesInvoiceItem, SalesInvoiceTax
    from .models.sales_order import SalesOrderItem


class SalesOrderCreate(BaseModel):
    """판매주문 생성 요청 스키마."""

    customer_id: str
    customer_name: str
    transaction_date: date
    delivery_date: date
    items: list[SalesOrderItem] = Field(default_factory=list)


class SalesOrderUpdate(BaseModel):
    """판매주문 수정 요청 스키마."""

    customer_id: str | None = None
    customer_name: str | None = None
    transaction_date: date | None = None
    delivery_date: date | None = None
    items: list[SalesOrderItem] | None = None


class DeliveryNoteCreate(BaseModel):
    """납품서 생성 요청 스키마."""

    customer_id: str
    customer_name: str
    posting_date: date
    sales_order_ref: str | None = None
    items: list[DeliveryNoteItem] = Field(default_factory=list)
    transporter: str | None = None


class DeliveryNoteUpdate(BaseModel):
    """납품서 수정 요청 스키마."""

    customer_id: str | None = None
    customer_name: str | None = None
    posting_date: date | None = None
    sales_order_ref: str | None = None
    items: list[DeliveryNoteItem] | None = None
    transporter: str | None = None


class SalesInvoiceCreate(BaseModel):
    """판매송장 생성 요청 스키마."""

    customer_id: str
    customer_name: str
    posting_date: date
    due_date: date
    sales_order_ref: str | None = None
    delivery_note_ref: str | None = None
    items: list[SalesInvoiceItem] = Field(default_factory=list)
    taxes: list[SalesInvoiceTax] = Field(default_factory=list)
    etax_invoice_ref: str | None = None


class SalesInvoiceUpdate(BaseModel):
    """판매송장 수정 요청 스키마."""

    customer_id: str | None = None
    customer_name: str | None = None
    posting_date: date | None = None
    due_date: date | None = None
    sales_order_ref: str | None = None
    delivery_note_ref: str | None = None
    items: list[SalesInvoiceItem] | None = None
    taxes: list[SalesInvoiceTax] | None = None
    etax_invoice_ref: str | None = None


_SELLING_DTO_TYPES = {
    "DeliveryNoteItem": __import__(
        "oneerp_selling_app.models.delivery_note", fromlist=["DeliveryNoteItem"]
    ).DeliveryNoteItem,
    "SalesInvoiceItem": __import__(
        "oneerp_selling_app.models.sales_invoice", fromlist=["SalesInvoiceItem"]
    ).SalesInvoiceItem,
    "SalesInvoiceTax": __import__(
        "oneerp_selling_app.models.sales_invoice", fromlist=["SalesInvoiceTax"]
    ).SalesInvoiceTax,
    "SalesOrderItem": __import__(
        "oneerp_selling_app.models.sales_order", fromlist=["SalesOrderItem"]
    ).SalesOrderItem,
}

SalesOrderCreate.model_rebuild(_types_namespace=_SELLING_DTO_TYPES)
SalesOrderUpdate.model_rebuild(_types_namespace=_SELLING_DTO_TYPES)
DeliveryNoteCreate.model_rebuild(_types_namespace=_SELLING_DTO_TYPES)
DeliveryNoteUpdate.model_rebuild(_types_namespace=_SELLING_DTO_TYPES)
SalesInvoiceCreate.model_rebuild(_types_namespace=_SELLING_DTO_TYPES)
SalesInvoiceUpdate.model_rebuild(_types_namespace=_SELLING_DTO_TYPES)
