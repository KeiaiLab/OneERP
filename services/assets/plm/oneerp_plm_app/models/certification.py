"""규격/인증(Certification) 문서 모델.

제품별 규격 및 인증(KC, CE, UL, RoHS 등) 정보를 관리한다.
인증 만료일 추적, 자동 알림, 갱신 워크플로우를 제공한다.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class CertType(StrEnum):
    """인증 유형."""

    KC_SAFETY = "kc_safety"
    KC_EMC = "kc_emc"
    KC_TELECOM = "kc_telecom"
    CE = "ce"
    UL = "ul"
    FCC = "fcc"
    ROHS = "rohs"
    REACH = "reach"
    WEEE = "weee"
    OTHER = "other"


class CertStatus(StrEnum):
    """인증 상태."""

    PENDING = "pending"
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class CertificationCreate(BaseModel):
    """인증 생성 요청 스키마."""

    product_id: str
    cert_type: CertType
    cert_number: str
    cert_name: str = Field(min_length=1, max_length=200)
    certifying_body: str
    issued_date: date
    expiry_date: date | None = None
    renewal_date: date | None = None
    scope: str = ""
    standard_reference: str | None = None
    test_report_url: str | None = None
    certificate_url: str | None = None
    responsible_person: str | None = None
    notes: str = ""


class CertificationUpdate(BaseModel):
    """인증 수정 요청 스키���."""

    cert_name: str | None = None
    certifying_body: str | None = None
    expiry_date: date | None = None
    renewal_date: date | None = None
    scope: str | None = None
    standard_reference: str | None = None
    test_report_url: str | None = None
    certificate_url: str | None = None
    responsible_person: str | None = None
    notes: str | None = None


class Certification(BaseDocument):
    """규격/인증 문서 — 제품별 인증 관리.

    naming prefix: CERT
    """

    product_id: str = Field(default="", description="대상 제품")
    cert_type: CertType = Field(default=CertType.OTHER, description="인증 유형")
    cert_number: str = Field(default="", description="인증 번호")
    cert_name: str = Field(default="", description="인증명")
    certifying_body: str = Field(default="", description="인증 기관")
    status: CertStatus = Field(default=CertStatus.ACTIVE, description="인증 상태")
    issued_date: date | None = Field(default=None, description="인증 취득일")
    expiry_date: date | None = Field(default=None, description="인증 만��일")
    renewal_date: date | None = Field(default=None, description="갱신 예정일")
    scope: str = Field(default="", description="인증 범위")
    standard_reference: str | None = Field(default=None, description="적용 규��")
    test_report_url: str | None = Field(default=None, description="시험 성적서 파일")
    certificate_url: str | None = Field(default=None, description="인증서 파일")
    alert_90d_sent: bool = Field(default=False, description="90일 전 알림 발송 여부")
    alert_60d_sent: bool = Field(default=False, description="60일 전 알림 발송 여���")
    alert_30d_sent: bool = Field(default=False, description="30일 전 알림 발송 여부")
    responsible_person: str | None = Field(default=None, description="인증 담당자")
    notes: str = Field(default="", description="비고")
    deleted_at: str | None = Field(default=None, description="삭제 시각")
