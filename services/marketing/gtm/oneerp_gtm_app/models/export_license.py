"""수출허가 모델 — 수출입 허가·승인 문서를 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ExportLicenseCreate(BaseModel):
    """수출허가 생성 요청 스키마."""

    license_type: str = "export"  # export/import/re_export
    applicant: str = ""
    destination_country: str = ""
    item_code: str = ""
    item_description: str = ""
    hs_code: str = ""
    quantity: Decimal = Decimal(0)
    uom: str = ""
    value_amount: Decimal = Decimal(0)
    currency: str = "KRW"
    purpose: str = ""


class ExportLicenseUpdate(BaseModel):
    """수출허가 수정 요청 스키마."""

    status: str | None = None
    destination_country: str | None = None
    quantity: Decimal | None = None
    value_amount: Decimal | None = None
    approved_date: date | None = None
    expiry_date: date | None = None
    remarks: str | None = None


class ExportLicense(BaseDocument):
    """수출허가 문서 — 수출입 허가 신청·승인 이력을 관리한다."""

    license_type: str = "export"
    applicant: str = ""
    destination_country: str = ""
    item_code: str = ""
    item_description: str = ""
    hs_code: str = ""
    quantity: Decimal = Decimal(0)
    uom: str = ""
    value_amount: Decimal = Decimal(0)
    currency: str = "KRW"
    purpose: str = ""
    status: str = "draft"  # draft/submitted/approved/rejected/expired
    approved_date: date | None = None
    expiry_date: date | None = None
    remarks: str = ""
