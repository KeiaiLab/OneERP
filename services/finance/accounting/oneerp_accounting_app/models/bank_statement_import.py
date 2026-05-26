"""은행 명세서 가져오기(BankStatementImport) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class BankStatementImportStatus(StrEnum):
    """은행 명세서 가져오기 상태."""

    DRAFT = "draft"
    IMPORTED = "imported"
    FAILED = "failed"


class BankStatementImportCreate(BaseModel):
    """은행 명세서 가져오기 생성 요청 스키마."""

    bank_account_id: str
    import_date: date | None = None
    file_name: str = ""
    total_transactions: int = 0
    imported_count: int = 0


class BankStatementImportUpdate(BaseModel):
    """은행 명세서 가져오기 수정 요청 스키마."""

    bank_account_id: str | None = None
    import_date: date | None = None
    file_name: str | None = None
    total_transactions: int | None = None
    imported_count: int | None = None


class BankStatementImport(BaseDocument):
    """은행 명세서 가져오기 문서."""

    status: BankStatementImportStatus = Field(
        default=BankStatementImportStatus.DRAFT,
        description="은행 명세서 가져오기 상태",
    )
    bank_account_id: str = ""
    import_date: date | None = None
    file_name: str = ""
    total_transactions: int = 0
    imported_count: int = 0
