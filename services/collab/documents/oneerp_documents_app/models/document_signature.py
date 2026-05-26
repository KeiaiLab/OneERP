"""전자서명(DocumentSignature) 모델 — 문서 전자서명/전자도장 기록.

BR-DOC-015: 서명 시점 문서 해시 무결성 검증.
BR-DOC-016: 서명 후 편집 금지.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class SignatureType(StrEnum):
    """서명 유형."""

    JOINT_CERTIFICATE = "joint_certificate"
    PRIVATE_CERTIFICATE = "private_certificate"
    ELECTRONIC_SEAL = "electronic_seal"


class DocumentSignatureCreate(BaseModel):
    """전자서명 생성 요청 스키마."""

    document_id: str = Field(description="문서 참조 ID")
    signature_type: SignatureType = Field(description="서명 유형")
    signature_data: str = Field(description="서명 데이터 (Base64)")
    certificate_info: dict[str, object] = Field(default_factory=dict, description="인증서 정보")
    certificate_serial: str | None = Field(default=None, description="인증서 시리얼")


class DocumentSignatureUpdate(BaseModel):
    """전자서명 수정 (무효화용) 스키마."""

    is_valid: bool | None = None
    invalidated_reason: str | None = None


class DocumentSignature(BaseDocument):
    """전자서명 엔티티.

    문서에 대한 전자서명/전자도장을 기록한다.
    공동인증서, 사설인증서, 전자도장 모두 지원한다.
    """

    document_id: str = ""
    document_version: int = 1
    signer: str = ""
    signature_type: SignatureType = SignatureType.JOINT_CERTIFICATE
    signature_data: str = ""
    certificate_info: dict[str, object] = Field(default_factory=dict)
    certificate_serial: str | None = None
    document_hash: str = ""
    timestamp_token: str | None = None
    signed_at: datetime | None = None
    is_valid: bool = True
    invalidated_reason: str | None = None
    invalidated_at: datetime | None = None
    invalidated_by: str | None = None
