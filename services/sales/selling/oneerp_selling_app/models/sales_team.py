"""영업 팀(SalesTeam) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SalesTeamCreate(BaseModel):
    """영업 팀 생성 요청 스키마."""

    team_name: str
    leader_id: str = ""
    member_ids: list[str] = Field(default_factory=list)


class SalesTeamUpdate(BaseModel):
    """영업 팀 수정 요청 스키마."""

    team_name: str | None = None
    leader_id: str | None = None
    member_ids: list[str] | None = None


class SalesTeam(BaseDocument):
    """영업 팀 문서."""

    team_name: str = ""
    leader_id: str = ""
    member_ids: list[str] = Field(default_factory=list)
