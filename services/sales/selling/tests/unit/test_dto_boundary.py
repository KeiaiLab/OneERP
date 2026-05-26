"""OE004: Create/Update DTO는 models/가 아닌 dto.py에 존재해야 한다."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DTO_FILE = ROOT / "oneerp_selling_app" / "dto.py"
SALES_ORDER_MODEL = ROOT / "oneerp_selling_app" / "models" / "sales_order.py"
DELIVERY_MODEL = ROOT / "oneerp_selling_app" / "models" / "delivery_note.py"
SINV_MODEL = ROOT / "oneerp_selling_app" / "models" / "sales_invoice.py"


def test_sales_order_create_update_가_dto에_있다() -> None:
    assert DTO_FILE.exists(), f"{DTO_FILE}가 없음"
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class SalesOrderCreate" in text
    assert "class SalesOrderUpdate" in text


def test_sales_order_model에는_dto가_없다() -> None:
    text = SALES_ORDER_MODEL.read_text(encoding="utf-8")
    assert "class SalesOrderCreate" not in text
    assert "class SalesOrderUpdate" not in text


def test_delivery_note_create_update가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class DeliveryNoteCreate" in text
    assert "class DeliveryNoteUpdate" in text


def test_delivery_note_model에는_dto가_없다() -> None:
    text = DELIVERY_MODEL.read_text(encoding="utf-8")
    assert "class DeliveryNoteCreate" not in text
    assert "class DeliveryNoteUpdate" not in text


def test_sales_invoice_create_update가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class SalesInvoiceCreate" in text
    assert "class SalesInvoiceUpdate" in text


def test_sales_invoice_model에는_dto가_없다() -> None:
    text = SINV_MODEL.read_text(encoding="utf-8")
    assert "class SalesInvoiceCreate" not in text
    assert "class SalesInvoiceUpdate" not in text
