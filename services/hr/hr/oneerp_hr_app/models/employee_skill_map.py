"""직원스킬맵(EmployeeSkillMap) 문서 모델 — HR 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class EmployeeSkillMapCreate(BaseModel):
    """직원스킬맵 생성 요청 스키마."""

    employee: str
    skills: dict = {}


class EmployeeSkillMapUpdate(BaseModel):
    """직원스킬맵 수정 요청 스키마."""

    employee: str | None = None
    skills: dict | None = None


class EmployeeSkillMap(BaseDocument):
    """직원스킬맵 문서 — HR 직원 역량 마스터.

    naming prefix: ESM
    """

    employee: str = ""
    skills: dict = {}
