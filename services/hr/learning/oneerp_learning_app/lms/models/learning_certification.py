"""교육 인증(LearningCertification) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class LearningCertificationCreate(BaseModel):
    """교육 인증 생성 요청 스키마."""

    employee_id: str
    course_id: str
    enrollment_id: str
    certification_name: str
    issued_date: date | None = None
    expiry_date: date | None = None
    is_mandatory: bool = False
    mandatory_law: str = ""
    status: str = "active"


class LearningCertificationUpdate(BaseModel):
    """교육 인증 수정 요청 스키마."""

    employee_id: str | None = None
    course_id: str | None = None
    enrollment_id: str | None = None
    certification_name: str | None = None
    issued_date: date | None = None
    expiry_date: date | None = None
    is_mandatory: bool | None = None
    mandatory_law: str | None = None
    status: str | None = None


class LearningCertification(BaseDocument):
    """교육 인증 문서."""

    employee_id: str = ""
    course_id: str = ""
    enrollment_id: str = ""
    certification_name: str = ""
    issued_date: date | None = None
    expiry_date: date | None = None
    is_mandatory: bool = False
    mandatory_law: str = ""
    status: str = "active"
