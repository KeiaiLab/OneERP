"""POS 프로필(POSProfile) 모델 정의."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class POSPaymentMode(BaseModel):
    """POS 결제 수단 설정."""

    mode_of_payment: str
    default: bool = False


class POSProfile(BaseDocument):
    """POS 프로필 문서 — POS 설정 프로필.

    naming prefix: POS
    """

    name: str = ""
    warehouse: str = ""
    price_list: str = ""
    write_off_account: str = ""
    payments: list[POSPaymentMode] = []


class POSProfileCreate(BaseModel):
    """POS 프로필 생성 요청 스키마."""

    name: str
    warehouse: str = ""
    price_list: str = ""
    write_off_account: str = ""
    payments: list[POSPaymentMode] = []


class POSProfileUpdate(BaseModel):
    """POS 프로필 수정 요청 스키마 — 모든 필드 선택적."""

    name: str | None = None
    warehouse: str | None = None
    price_list: str | None = None
    write_off_account: str | None = None
    payments: list[POSPaymentMode] | None = None
