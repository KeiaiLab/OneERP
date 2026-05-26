"""자금 이체(FundTransfer) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator, model_validator


class FundTransferStatus(StrEnum):
    """자금 이체 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    COMPLETED = "completed"


class FundTransferCreate(BaseModel):
    """자금 이체 생성 요청 스키마.

    BR-TRS-001: 이체 금액은 양수여야 한다.
    BR-TRS-002: 출금 계좌와 입금 계좌는 달라야 한다.
    """

    from_account: str
    to_account: str
    amount: Decimal = Decimal(0)
    currency: str = "KRW"
    transfer_date: date | None = None
    reference: str = ""

    @field_validator("amount")
    @classmethod
    def _amount_must_be_positive(cls, v: Decimal) -> Decimal:
        """BR-TRS-001: 이체 금액은 0보다 커야 한다."""
        if v <= 0:
            msg = "이체 금액은 0보다 커야 합니다"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _accounts_must_differ(self) -> FundTransferCreate:
        """BR-TRS-002: 출금 계좌와 입금 계좌는 동일할 수 없다."""
        if self.from_account and self.to_account and self.from_account == self.to_account:
            msg = "출금 계좌와 입금 계좌가 동일합니다"
            raise ValueError(msg)
        return self


class FundTransferUpdate(BaseModel):
    """자금 이체 수정 요청 스키마."""

    from_account: str | None = None
    to_account: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    transfer_date: date | None = None
    reference: str | None = None


class FundTransfer(BaseDocument):
    """자금 이체 문서."""

    status: FundTransferStatus = Field(
        default=FundTransferStatus.DRAFT,
        description="자금 이체 상태",
    )
    from_account: str = ""
    to_account: str = ""
    amount: Decimal = Decimal(0)
    currency: str = "KRW"
    transfer_date: date | None = None
    reference: str = ""
