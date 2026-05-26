"""테넌트(Tenant) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class TenantPlan(StrEnum):
    """테넌트 구독 플랜."""

    STARTER = "starter"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"


class TenantCreate(BaseModel):
    """테넌트 생성 요청 스키마."""

    tenant_name: str = Field(description="테넌트명")
    domain: str = Field(default="", description="도메인")
    is_active: bool = Field(default=True, description="활성 여부")
    plan: TenantPlan = Field(default=TenantPlan.STANDARD, description="구독 플랜")
    allowed_modules: list[str] = Field(default_factory=list, description="허용 모듈 목록")
    max_users: int = Field(default=50, description="최대 사용자 수")
    admin_user_id: str = Field(default="", description="관리자 사용자 ID")
    contact_email: str = Field(default="", description="연락처 이메일")
    contract_start: date | None = Field(default=None, description="계약 시작일")
    contract_end: date | None = Field(default=None, description="계약 종료일")


class TenantUpdate(BaseModel):
    """테넌트 수정 요청 스키마."""

    tenant_name: str | None = Field(default=None, description="테넌트명")
    domain: str | None = Field(default=None, description="도메인")
    is_active: bool | None = Field(default=None, description="활성 여부")
    plan: TenantPlan | None = Field(default=None, description="구독 플랜")
    allowed_modules: list[str] | None = Field(default=None, description="허용 모듈 목록")
    max_users: int | None = Field(default=None, description="최대 사용자 수")
    admin_user_id: str | None = Field(default=None, description="관리자 사용자 ID")
    contact_email: str | None = Field(default=None, description="연락처 이메일")
    contract_start: date | None = Field(default=None, description="계약 시작일")
    contract_end: date | None = Field(default=None, description="계약 종료일")
    suspended_at: datetime | None = Field(default=None, description="정지 일시")
    suspended_reason: str | None = Field(default=None, description="정지 사유")


class Tenant(BaseDocument):
    """테넌트 문서 — Setup 테넌트 마스터.

    naming prefix: TNT
    """

    tenant_name: str = Field(default="", description="테넌트명")
    domain: str = Field(default="", description="도메인")
    is_active: bool = Field(default=True, description="활성 여부")
    plan: TenantPlan = Field(default=TenantPlan.STANDARD, description="구독 플랜")
    allowed_modules: list[str] = Field(default_factory=list, description="허용 모듈 목록")
    max_users: int = Field(default=50, description="최대 사용자 수")
    admin_user_id: str = Field(default="", description="관리자 사용자 ID")
    contact_email: str = Field(default="", description="연락처 이메일")
    contract_start: date | None = Field(default=None, description="계약 시작일")
    contract_end: date | None = Field(default=None, description="계약 종료일")
    suspended_at: datetime | None = Field(default=None, description="정지 일시")
    suspended_reason: str = Field(default="", description="정지 사유")


_TENANT_TYPES = {
    "date": __import__("datetime").date,
    "datetime": __import__("datetime").datetime,
}

TenantCreate.model_rebuild(_types_namespace=_TENANT_TYPES)
TenantUpdate.model_rebuild(_types_namespace=_TENANT_TYPES)
Tenant.model_rebuild(_types_namespace=_TENANT_TYPES)
