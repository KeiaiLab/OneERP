"""인명부(EmployeeDirectory) 엔트리 모델 — 조직도/인명부 모듈.

BR-DIR-008: 인명부 엔트리는 직원(employee_id)과 조직 단위에 연결되어야 한다.
BR-DIR-009: 동일 직원은 동일 시점에 하나의 주 소속(is_primary=True)만 가진다.
BR-DIR-010: 인명부 상태 변경 시 이벤트를 발행한다.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from datetime import date


class DirectoryEntryStatus(StrEnum):
    """인명부 엔트리 상태."""

    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TRANSFERRED = "transferred"
    RESIGNED = "resigned"


class EmployeeDirectoryCreate(BaseModel):
    """인명부 엔트리 생성 요청 스키마.

    BR-DIR-008: employee_id와 org_unit_id는 필수이다.
    """

    employee_id: str
    employee_name: str
    org_id: str = ""
    org_unit_id: str
    position_id: str = ""
    designation: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    office_location: str = ""
    is_primary: bool = True
    effective_from: date | None = None

    @field_validator("employee_id")
    @classmethod
    def employee_id_required(cls, v: str) -> str:
        """BR-DIR-008: 직원 ID는 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-009: 직원 ID는 필수입니다"
            raise ValueError(msg)
        return v.strip()

    @field_validator("org_unit_id")
    @classmethod
    def org_unit_id_required(cls, v: str) -> str:
        """BR-DIR-008: 조직 단위 ID는 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-010: 조직 단위 ID는 필수입니다"
            raise ValueError(msg)
        return v.strip()


class EmployeeDirectoryUpdate(BaseModel):
    """인명부 엔트리 수정 요청 스키마."""

    employee_name: str | None = None
    org_id: str | None = None
    org_unit_id: str | None = None
    position_id: str | None = None
    designation: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    office_location: str | None = None
    is_primary: bool | None = None
    effective_from: date | None = None
    status: DirectoryEntryStatus | None = None


class EmployeeDirectory(BaseDocument):
    """인명부 엔트리 — 직원의 조직 소속 정보.

    naming prefix: EDIR
    BR-DIR-008, BR-DIR-009, BR-DIR-010
    """

    employee_id: str = Field(default="", description="직원 ID")
    employee_name: str = Field(default="", description="직원명")
    org_id: str = Field(default="", description="소속 조직 ID")
    org_unit_id: str = Field(default="", description="소속 조직 단위 ID")
    position_id: str = Field(default="", description="직위 ID")
    designation: str = Field(default="", description="직책")
    email: str = Field(default="", description="이메일")
    phone: str = Field(default="", description="전화번호")
    mobile: str = Field(default="", description="휴대전화")
    office_location: str = Field(default="", description="근무지")
    is_primary: bool = Field(default=True, description="주 소속 여부")
    effective_from: date | None = Field(default=None, description="발효일")
    status: DirectoryEntryStatus = Field(default=DirectoryEntryStatus.ACTIVE, description="상태")
