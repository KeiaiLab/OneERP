"""직원(Employee) 문서 모델 — HR 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EmployeeStatus(StrEnum):
    """직원 재직 상태."""

    ACTIVE = "active"
    LEFT = "left"
    SUSPENDED = "suspended"


class EmployeeCreate(BaseModel):
    """직원 생성 요청 스키마."""

    employee_name: str
    department: str = ""
    designation: str = ""
    date_of_joining: date | None = None
    date_of_birth: date | None = None
    employment_type: str = "REGULAR"
    reports_to: str = ""
    gender: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""


class EmployeeUpdate(BaseModel):
    """직원 수정 요청 스키마."""

    employee_name: str | None = None
    department: str | None = None
    designation: str | None = None
    date_of_joining: date | None = None
    date_of_birth: date | None = None
    employment_type: str | None = None
    reports_to: str | None = None
    status: EmployeeStatus | None = None
    gender: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None


class Employee(BaseDocument):
    """직원 문서 — HR 직원 정보.

    naming prefix: EMP
    """

    employee_name: str = Field(default="", description="직원명")
    department: str = Field(default="", description="부서")
    designation: str = Field(default="", description="직위")
    date_of_joining: date | None = Field(default=None, description="입사일")
    date_of_birth: date | None = Field(default=None, description="생년월일")
    employment_type: str = Field(default="REGULAR", description="고용 유형")
    reports_to: str = Field(default="", description="직속 상사 직원 ID")
    status: EmployeeStatus = Field(default=EmployeeStatus.ACTIVE, description="재직 상태")
    gender: str = Field(default="", description="성별")
    email: str = Field(default="", description="이메일")
    phone: str = Field(default="", description="전화번호")
    company: str = Field(default="", description="소속 회사")
