"""운송사(Carrier) 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ApiIntegration(BaseModel):
    """택배사 API 연동 설정."""

    enabled: bool = False
    provider: str = ""
    api_key: str = ""
    api_url: str = ""
    webhook_url: str = ""


class SettlementTerms(BaseModel):
    """정산 조건."""

    payment_days: int = 30
    cutoff_day: int = 25
    settlement_cycle: str = "monthly"


class Address(BaseModel):
    """주소 정보."""

    zipcode: str = ""
    address1: str = ""
    address2: str = ""
    city: str = ""
    province: str = ""


class CarrierCreate(BaseModel):
    """운송사 생성 요청."""

    carrier_name: str
    carrier_type: str  # express/freight/own_fleet/parcel
    business_no: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    address: Address | None = None
    api_integration: ApiIntegration | None = None
    tracking_url_template: str | None = None
    settlement_terms: SettlementTerms | None = None
    is_active: bool = True
    company: str = ""


class CarrierUpdate(BaseModel):
    """운송사 수정 요��."""

    carrier_name: str | None = None
    carrier_type: str | None = None
    business_no: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    address: Address | None = None
    api_integration: ApiIntegration | None = None
    tracking_url_template: str | None = None
    settlement_terms: SettlementTerms | None = None
    is_active: bool | None = None
    company: str | None = None


class Carrier(BaseDocument):
    """운송사 마스터 — 운송 서비스 제공 업체 정보.

    naming prefix: CRR
    """

    carrier_name: str = Field(default="", description="운송사명")
    carrier_type: str = Field(default="", description="유형: express/freight/own_fleet/parcel")
    business_no: str | None = Field(default=None, description="사업자등록번호")
    contact_name: str | None = Field(default=None, description="담당자명")
    contact_phone: str | None = Field(default=None, description="담당자 연락처")
    contact_email: str | None = Field(default=None, description="담당자 이메일")
    address: Address | None = Field(default=None, description="주소")
    api_integration: ApiIntegration | None = Field(default=None, description="API 연동 설정")
    tracking_url_template: str | None = Field(default=None, description="추적 URL 템플릿")
    settlement_terms: SettlementTerms | None = Field(default=None, description="정��� 조건")
    performance_score: float = Field(default=0.0, description="성과 점수 (0.0~5.0)")
    is_active: bool = Field(default=True, description="활성 여부")
    company: str = Field(default="", description="회사")
