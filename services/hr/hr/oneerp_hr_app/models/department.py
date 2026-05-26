"""부서(Department) 문서 모델 — HR 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    """부서 생성 요청 스키마."""

    department_name: str
    parent_department: str | None = None
    is_group: bool = False
    company: str = ""


class DepartmentUpdate(BaseModel):
    """부서 수정 요청 스키마."""

    department_name: str | None = None
    parent_department: str | None = None
    is_group: bool | None = None
    company: str | None = None


class Department(BaseDocument):
    """부서 문서 — HR 조직 구조.

    naming prefix: DEPT
    """

    department_name: str = Field(default="", description="부서명")
    parent_department: str | None = Field(default=None, description="상위 부서")
    is_group: bool = Field(default=False, description="그룹 여부")
    company: str = Field(default="", description="소속 회사")
