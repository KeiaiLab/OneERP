"""회사(Company) 모델 정의."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class Company(BaseDocument):
    """회사 문서 — 기업 마스터 데이터.

    naming prefix: COMP
    """

    company_name: str = Field(description="회사명")
    abbr: str = Field(description="약칭")
    company_code: str = Field(default="", description="회사 코드")
    business_registration_number: str = Field(default="", description="사업자등록번호")
    representative_name: str = Field(default="", description="대표자명")
    address: str = Field(default="", description="주소")
    default_currency: str = Field(default="KRW", description="기본 통화")
    country: str = Field(default="KR", description="국가 코드")
    chart_of_accounts: str = Field(default="", description="계정과목 체계")
    fiscal_year_start: str = Field(default="01-01", description="회계연도 시작일")
    domain: str = Field(default="", description="사업 도메인")
    parent_company_id: str = Field(default="", description="상위 회사 ID")
    is_default: bool = Field(default=False, description="기본 회사 여부")
    is_active: bool = Field(default=True, description="활성 여부")


class CompanyCreate(BaseModel):
    """회사 생성 요청 스키마."""

    company_name: str
    abbr: str
    company_code: str = ""
    business_registration_number: str = ""
    representative_name: str = ""
    address: str = ""
    default_currency: str = "KRW"
    country: str = "KR"
    chart_of_accounts: str = ""
    fiscal_year_start: str = "01-01"
    domain: str = ""
    parent_company_id: str = ""
    is_default: bool = False
    is_active: bool = True


class CompanyUpdate(BaseModel):
    """회사 수정 요청 스키마 — 모든 필드 선택적."""

    company_name: str | None = None
    abbr: str | None = None
    company_code: str | None = None
    business_registration_number: str | None = None
    representative_name: str | None = None
    address: str | None = None
    default_currency: str | None = None
    country: str | None = None
    chart_of_accounts: str | None = None
    fiscal_year_start: str | None = None
    domain: str | None = None
    parent_company_id: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None
