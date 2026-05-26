"""계정과목(Chart of Accounts) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class AccountType(StrEnum):
    """계정과목 유형."""

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"


class AccountCreate(BaseModel):
    """계정과목 생성 요청 스키마."""

    account_name: str
    account_type: AccountType
    parent_account: str | None = None
    is_group: bool = False
    currency: str = "KRW"


class AccountUpdate(BaseModel):
    """계정과목 수정 요청 스키마."""

    account_name: str | None = None
    account_type: AccountType | None = None
    parent_account: str | None = None
    is_group: bool | None = None
    currency: str | None = None


class Account(BaseDocument):
    """계정과목 문서 — 재무제표의 기본 구성 단위.

    naming prefix: ACC
    """

    account_name: str = Field(default="", description="계정과목명")
    account_type: AccountType = Field(default=AccountType.ASSET, description="계정 유형")
    parent_account: str | None = Field(default=None, description="상위 계정과목")
    is_group: bool = Field(default=False, description="그룹 여부")
    currency: str = Field(default="KRW", description="통화")
