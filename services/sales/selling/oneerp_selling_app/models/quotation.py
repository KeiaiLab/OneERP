"""견적서(Quotation) 문서 모델."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field


class QuotationItem(LineItem):
    """견적서 라인 아이템."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(description="품목명")
    qty: Decimal = Field(description="수량")
    rate: Decimal = Field(description="단가")
    amount: Decimal = Field(default=Decimal(0), description="금액 (수량 x 단가)")


class QuotationCreate(BaseModel):
    """견적서 생성 요청 스키마."""

    customer_id: str
    customer_name: str
    transaction_date: date
    valid_till: date | None = None
    price_list_id: str | None = None
    items: list[QuotationItem] = []


class QuotationUpdate(BaseModel):
    """견적서 수정 요청 스키마."""

    customer_id: str | None = None
    customer_name: str | None = None
    transaction_date: date | None = None
    valid_till: date | None = None
    price_list_id: str | None = None
    items: list[QuotationItem] | None = None


class QuotationEmailDelivery(BaseModel):
    """견적서 메일 발송 기록."""

    recipient_email: str = ""
    subject: str = ""
    message: str = ""
    sent_at: datetime | None = None
    pdf_file_name: str = ""


class QuotationCustomerSignature(BaseModel):
    """고객 포털 전자서명 기록."""

    signer_name: str = ""
    signer_email: str = ""
    signature_text: str = ""
    signature_type: str = "typed"
    signed_at: datetime | None = None


class QuotationSendEmailRequest(BaseModel):
    """견적서 메일 발송 요청."""

    recipient_email: str
    subject: str
    message: str = ""


class QuotationPortalSignRequest(BaseModel):
    """포털 전자서명 요청."""

    token: str
    signer_name: str
    signer_email: str
    signature_text: str
    signature_type: str = "typed"


class Quotation(BaseDocument):
    """견적서 문서 — 고객에게 제공하는 가격 제안서.

    naming prefix: QTN
    """

    customer_id: str = Field(default="", description="고객 ID")
    customer_name: str = Field(default="", description="고객명 (비정규화)")
    transaction_date: date | None = Field(default=None, description="거래일자")
    valid_till: date | None = Field(default=None, description="견적 유효기한")
    price_list_id: str | None = Field(default=None, description="적용 가격표 ID")
    price_list_name: str | None = Field(default=None, description="적용 가격표명")
    currency: str = Field(default="KRW", description="견적 통화")
    items: list[QuotationItem] = Field(default_factory=list, description="견적 라인 아이템 목록")
    total: Decimal = Field(default=Decimal(0), description="세전 합계 금액")
    grand_total: Decimal = Field(default=Decimal(0), description="세후 총 금액")
    email_delivery: QuotationEmailDelivery | None = Field(
        default=None, description="메일 발송 기록"
    )
    portal_access_token: str = Field(default="", description="포털 서명 토큰")
    portal_access_expires_at: datetime | None = Field(
        default=None,
        description="포털 서명 토큰 만료 시각",
    )
    signature_status: str = Field(default="not_requested", description="고객 서명 상태")
    customer_signature: QuotationCustomerSignature | None = Field(
        default=None,
        description="고객 전자서명 정보",
    )
