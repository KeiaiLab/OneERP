"""위키 공간(WikiSpace) 문서 모델 — 위키 모듈.

위키 공간은 위키 페이지를 그룹화하는 최상위 컨테이너이다.
부서별, 프로젝트별 등 목적에 따라 공간을 분리한다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WikiSpaceVisibility(StrEnum):
    """위키 공간 공개 범위."""

    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class WikiSpaceCreate(BaseModel):
    """위키 공간 생성 요청 스키마."""

    name: str
    description: str = ""
    visibility: WikiSpaceVisibility = WikiSpaceVisibility.PUBLIC
    owner_id: str = ""


class WikiSpaceUpdate(BaseModel):
    """위키 공간 수정 요청 스키마."""

    name: str | None = None
    description: str | None = None
    visibility: WikiSpaceVisibility | None = None
    owner_id: str | None = None


class WikiSpace(BaseDocument):
    """위키 공간 — 위키 페이지의 논리적 컨테이너.

    naming prefix: WS
    """

    name: str = Field(default="", description="공간 이름")
    description: str = Field(default="", description="공간 설명")
    visibility: WikiSpaceVisibility = Field(
        default=WikiSpaceVisibility.PUBLIC,
        description="공개 범위",
    )
    owner_id: str = Field(default="", description="소유자 ID")
    page_count: int = Field(default=0, description="페이지 수")
