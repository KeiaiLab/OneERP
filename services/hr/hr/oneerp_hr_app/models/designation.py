"""직급(Designation) 문서 모델 — HR 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DesignationCreate(BaseModel):
    """직급 생성 요청 스키마."""

    title: str
    description: str = ""
    rank_order: int = 0
    is_active: bool = True


class DesignationUpdate(BaseModel):
    """직급 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    rank_order: int | None = None
    is_active: bool | None = None


class Designation(BaseDocument):
    """직급 문서 — HR 직급 마스터.

    naming prefix: DESG
    """

    title: str = Field(default="", description="직급명")
    description: str = Field(default="", description="직급 설명")
    rank_order: int = Field(default=0, description="직급 정렬 순서")
    is_active: bool = Field(default=True, description="사용 여부")
