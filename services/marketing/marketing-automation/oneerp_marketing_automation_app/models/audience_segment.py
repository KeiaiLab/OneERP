"""오디언스 세그먼트 모델 — 타겟 고객 세그먼트 정의와 관리."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AudienceSegmentCreate(BaseModel):
    """오디언스 세그먼트 생성 요청 스키마."""

    segment_name: str
    segment_type: str = "static"  # static/dynamic/lookalike
    criteria: dict = {}  # 필터 조건 (age_range, location, behavior 등)
    source: str = ""  # crm/website/import
    description: str = ""
    tags: list[str] = []


class AudienceSegmentUpdate(BaseModel):
    """오디언스 세그먼트 수정 요청 스키마."""

    segment_name: str | None = None
    criteria: dict | None = None
    description: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class AudienceSegment(BaseDocument):
    """오디언스 세그먼트 문서 — 타겟 고객 세그먼트 정보를 저장한다."""

    segment_name: str = ""
    segment_type: str = "static"
    criteria: dict = {}
    source: str = ""
    description: str = ""
    tags: list[str] = []
    is_active: bool = True
    member_count: int = 0
    last_refreshed_at: str = ""
