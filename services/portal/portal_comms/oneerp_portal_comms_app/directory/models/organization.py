"""법인/조직(Organization) 마스터 모델 — 조직도/인명부 모듈.

BR-DIR-001: 조직은 고유한 코드와 명칭을 가져야 한다.
BR-DIR-002: 조직은 활성/비활성 상태를 가진다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class OrgStatus(StrEnum):
    """조직 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class OrganizationCreate(BaseModel):
    """조직 생성 요청 스키마.

    BR-DIR-001: org_code와 org_name은 필수이다.
    """

    org_code: str
    org_name: str
    org_name_en: str = ""
    parent_org_id: str | None = None
    representative: str = ""
    business_number: str = ""
    address: str = ""
    phone: str = ""
    industry: str = ""

    @field_validator("org_code")
    @classmethod
    def org_code_not_empty(cls, v: str) -> str:
        """BR-DIR-001: 조직 코드는 비어있을 수 없다."""
        if not v.strip():
            msg = "ERR-DIR-001: 조직 코드는 필수입니다"
            raise ValueError(msg)
        return v.strip()

    @field_validator("org_name")
    @classmethod
    def org_name_not_empty(cls, v: str) -> str:
        """BR-DIR-001: 조직 명칭은 비어있을 수 없다."""
        if not v.strip():
            msg = "ERR-DIR-002: 조직 명칭은 필수입니다"
            raise ValueError(msg)
        return v.strip()


class OrganizationUpdate(BaseModel):
    """조직 수정 요청 스키마."""

    org_code: str | None = None
    org_name: str | None = None
    org_name_en: str | None = None
    parent_org_id: str | None = None
    representative: str | None = None
    business_number: str | None = None
    address: str | None = None
    phone: str | None = None
    industry: str | None = None
    status: OrgStatus | None = None


class Organization(BaseDocument):
    """법인/조직 마스터 — 최상위 조직 단위.

    naming prefix: ORG
    BR-DIR-001, BR-DIR-002
    """

    org_code: str = Field(default="", description="조직 고유 코드")
    org_name: str = Field(default="", description="조직 명칭")
    org_name_en: str = Field(default="", description="조직 영문 명칭")
    parent_org_id: str | None = Field(default=None, description="상위 조직 ID")
    representative: str = Field(default="", description="대표자")
    business_number: str = Field(default="", description="사업자 번호")
    address: str = Field(default="", description="주소")
    phone: str = Field(default="", description="전화번호")
    industry: str = Field(default="", description="업종")
    status: OrgStatus = Field(default=OrgStatus.ACTIVE, description="상태")
