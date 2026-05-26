"""은행 피드(BankFeed) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class BankFeedStatus(StrEnum):
    """은행 피드 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class BankFeedCreate(BaseModel):
    """은행 피드 생성 요청 스키마."""

    bank_name: str
    account_number: str = ""
    last_sync_date: date | None = None
    sync_frequency: str = ""
    is_active: bool = True


class BankFeedUpdate(BaseModel):
    """은행 피드 수정 요청 스키마."""

    bank_name: str | None = None
    account_number: str | None = None
    last_sync_date: date | None = None
    sync_frequency: str | None = None
    is_active: bool | None = None


class BankFeed(BaseDocument):
    """은행 피드 문서."""

    status: BankFeedStatus = Field(
        default=BankFeedStatus.ACTIVE,
        description="은행 피드 상태",
    )
    bank_name: str = ""
    account_number: str = ""
    last_sync_date: date | None = None
    sync_frequency: str = ""
    is_active: bool = True


_BANK_FEED_TYPES = {"date": __import__("datetime").date}

BankFeedCreate.model_rebuild(_types_namespace=_BANK_FEED_TYPES)
BankFeedUpdate.model_rebuild(_types_namespace=_BANK_FEED_TYPES)
BankFeed.model_rebuild(_types_namespace=_BANK_FEED_TYPES)
