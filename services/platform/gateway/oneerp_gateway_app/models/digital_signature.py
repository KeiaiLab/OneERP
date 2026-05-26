"""전자서명(DigitalSignature) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class DigitalSignatureCreate(BaseModel):
    """전자서명 생성 요청 스키마."""

    signer: str
    document_id: str = ""
    signature_date: date | None = None
    signature_type: str = ""
    is_valid: bool = True


class DigitalSignatureUpdate(BaseModel):
    """전자서명 수정 요청 스키마."""

    signer: str | None = None
    document_id: str | None = None
    signature_date: date | None = None
    signature_type: str | None = None
    is_valid: bool | None = None


class DigitalSignature(BaseDocument):
    """전자서명 문서."""

    signer: str = ""
    document_id: str = ""
    signature_date: date | None = None
    signature_type: str = ""
    is_valid: bool = True


_DIGITAL_SIGNATURE_TYPES = {"date": __import__("datetime").date}

DigitalSignatureCreate.model_rebuild(_types_namespace=_DIGITAL_SIGNATURE_TYPES)
DigitalSignatureUpdate.model_rebuild(_types_namespace=_DIGITAL_SIGNATURE_TYPES)
DigitalSignature.model_rebuild(_types_namespace=_DIGITAL_SIGNATURE_TYPES)
