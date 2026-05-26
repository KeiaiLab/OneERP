"""조직도 스냅샷(OrgChartSnapshot) 모델 — 조직도/인명부 모듈.

BR-DIR-011: 조직도 스냅샷은 특정 시점의 조직 구조를 보존한다.
BR-DIR-012: 스냅샷 생성 시 모든 활성 조직 단위와 인명부를 포함한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from datetime import date


class OrgChartSnapshotCreate(BaseModel):
    """조직도 스냅샷 생성 요청 스키마.

    BR-DIR-011: org_id와 snapshot_date는 필수이다.
    """

    org_id: str
    snapshot_date: date
    description: str = ""

    @field_validator("org_id")
    @classmethod
    def org_id_required(cls, v: str) -> str:
        """BR-DIR-011: 조직 ID는 필수이다."""
        if not v.strip():
            msg = "ERR-DIR-011: 조직 ID는 필수입니다"
            raise ValueError(msg)
        return v.strip()


class OrgChartSnapshotUpdate(BaseModel):
    """조직도 스냅샷 수정 요청 스키마."""

    description: str | None = None


class OrgChartSnapshot(BaseDocument):
    """조직도 스냅샷 — 특정 시점의 조직 구조 보존.

    naming prefix: SNAP
    BR-DIR-011, BR-DIR-012
    """

    org_id: str = Field(default="", description="조직 ID")
    snapshot_date: date | None = Field(default=None, description="스냅샷 일자")
    description: str = Field(default="", description="설명")
    tree_data: list[dict[str, Any]] = Field(default_factory=list, description="조직 트리 데이터")
    total_units: int = Field(default=0, description="총 조직 단위 수")
    total_employees: int = Field(default=0, description="총 인원 수")
