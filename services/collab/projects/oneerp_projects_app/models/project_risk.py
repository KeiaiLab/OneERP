"""프로젝트 리스크(ProjectRisk) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ProjectRiskCreate(BaseModel):
    """프로젝트 리스크 생성 요청 스키마."""

    project_id: str
    risk_name: str = ""
    probability: str = ""
    impact: str = ""
    mitigation: str = ""
    owner: str = ""


class ProjectRiskUpdate(BaseModel):
    """프로젝트 리스크 수정 요청 스키마."""

    project_id: str | None = None
    risk_name: str | None = None
    probability: str | None = None
    impact: str | None = None
    mitigation: str | None = None
    owner: str | None = None


class ProjectRisk(BaseDocument):
    """프로젝트 리스크 문서."""

    project_id: str = ""
    risk_name: str = ""
    probability: str = ""
    impact: str = ""
    mitigation: str = ""
    owner: str = ""
