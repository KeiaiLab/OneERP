"""OE004: models/ 에는 Create/Update DTO가 없어야 하고 dto.py 로 격리한다."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DTO_FILE = ROOT / "oneerp_stock_app" / "dto.py"
ITEM_MODEL = ROOT / "oneerp_stock_app" / "models" / "item.py"
PR_MODEL = ROOT / "oneerp_stock_app" / "models" / "purchase_receipt.py"


def test_item_create_update가_dto에_있다() -> None:
    assert DTO_FILE.exists()
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class ItemCreate" in text
    assert "class ItemUpdate" in text


def test_item_model에는_dto가_없다() -> None:
    text = ITEM_MODEL.read_text(encoding="utf-8")
    assert "class ItemCreate" not in text
    assert "class ItemUpdate" not in text


def test_purchase_receipt_create_update가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class PurchaseReceiptCreate" in text
    assert "class PurchaseReceiptUpdate" in text


def test_purchase_receipt_model에는_dto가_없다() -> None:
    text = PR_MODEL.read_text(encoding="utf-8")
    assert "class PurchaseReceiptCreate" not in text
    assert "class PurchaseReceiptUpdate" not in text
