"""OE004: Create/Update DTO는 models/가 아닌 dto.py에 존재해야 한다."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DTO_FILE = ROOT / "oneerp_accounting_app" / "dto.py"
JE_MODEL = ROOT / "oneerp_accounting_app" / "models" / "journal_entry.py"
AR_MODEL = ROOT / "oneerp_accounting_app" / "models" / "accounts_receivable.py"


def test_journal_entry_create_update가_dto에_있다() -> None:
    assert DTO_FILE.exists()
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class JournalEntryCreate" in text
    assert "class JournalEntryUpdate" in text


def test_journal_entry_model에는_dto가_없다() -> None:
    text = JE_MODEL.read_text(encoding="utf-8")
    assert "class JournalEntryCreate" not in text
    assert "class JournalEntryUpdate" not in text


def test_accounts_receivable_create가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class AccountsReceivableCreate" in text


def test_accounts_receivable_model에는_dto가_없다() -> None:
    text = AR_MODEL.read_text(encoding="utf-8")
    assert "class AccountsReceivableCreate" not in text
