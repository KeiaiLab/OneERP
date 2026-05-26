"""원산지증명서 모델 — FTA 특혜관세 적용을 위한 원산지 증명 관리."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class OriginCertificateCreate(BaseModel):
    """원산지증명서 생성 요청 스키마."""

    certificate_type: str = "preferential"  # preferential/non_preferential
    agreement_code: str = ""
    exporter: str = ""
    importer: str = ""
    origin_country: str = "KR"
    destination_country: str = ""
    item_code: str = ""
    item_description: str = ""
    hs_code: str = ""
    fob_value: Decimal = Decimal(0)
    currency: str = "KRW"
    origin_criterion: str = ""  # WO/PE/PSR/RVC 등


class OriginCertificateUpdate(BaseModel):
    """원산지증명서 수정 요청 스키마."""

    status: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    certificate_number: str | None = None
    remarks: str | None = None


class OriginCertificate(BaseDocument):
    """원산지증명서 문서 — FTA 원산지 증명 발급·관리 이력을 저장한다."""

    certificate_type: str = "preferential"
    agreement_code: str = ""
    exporter: str = ""
    importer: str = ""
    origin_country: str = "KR"
    destination_country: str = ""
    item_code: str = ""
    item_description: str = ""
    hs_code: str = ""
    fob_value: Decimal = Decimal(0)
    currency: str = "KRW"
    origin_criterion: str = ""
    status: str = "draft"  # draft/issued/verified/rejected/expired
    certificate_number: str = ""
    issue_date: date | None = None
    expiry_date: date | None = None
    remarks: str = ""
