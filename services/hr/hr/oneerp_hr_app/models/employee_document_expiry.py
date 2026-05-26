"""직원 서류 만료(EmployeeDocumentExpiry) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EmployeeDocumentExpiryStatus(StrEnum):
    """직원 자격증/면허 만료 관리 상태."""

    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    RENEWED = "renewed"


class EmployeeDocumentExpiryCreate(BaseModel):
    """직원 서류 만료 생성 요청 스키마."""

    employee_id: str
    document_type: str = ""
    document_name: str = ""
    expiry_date: date | None = None
    is_notified: bool = False


class EmployeeDocumentExpiryUpdate(BaseModel):
    """직원 서류 만료 수정 요청 스키마."""

    employee_id: str | None = None
    document_type: str | None = None
    document_name: str | None = None
    expiry_date: date | None = None
    is_notified: bool | None = None
    status: EmployeeDocumentExpiryStatus | None = None


class EmployeeDocumentExpiry(BaseDocument):
    """직원 서류 만료 문서."""

    status: EmployeeDocumentExpiryStatus = Field(
        default=EmployeeDocumentExpiryStatus.ACTIVE,
        description="직원 자격증/면허 만료 관리 상태",
    )
    employee_id: str = ""
    document_type: str = ""
    document_name: str = ""
    expiry_date: date | None = None
    is_notified: bool = False
