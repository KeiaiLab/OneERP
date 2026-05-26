"""도면(Drawing) 문서 모델.

CAD 파일, 도면 PDF, 사양서 등 엔지니어링 문서를 버전 관리한다.
체크인/체크아웃으로 동시 편집을 방지한다.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class DrawingType(StrEnum):
    """도면 유형."""

    PART_DRAWING = "part_drawing"
    ASSEMBLY_DRAWING = "assembly_drawing"
    SCHEMATIC = "schematic"
    SPECIFICATION = "specification"
    TEST_REPORT = "test_report"
    SOP = "sop"
    OTHER = "other"


class DrawingStatus(StrEnum):
    """도면 상태."""

    WORK_IN_PROGRESS = "work_in_progress"
    IN_REVIEW = "in_review"
    RELEASED = "released"
    OBSOLETE = "obsolete"


class RevisionEntry(BaseModel):
    """리비전 이력 — 임베디드 모델."""

    revision: str = Field(description="리비전")
    file_url: str = Field(description="파일 URL")
    eco_id: str | None = Field(default=None, description="변경 사유 ECO ID")
    change_summary: str = Field(default="", description="변경 요약")
    released_by: str | None = Field(default=None, description="릴리즈 승인자")
    released_at: datetime | None = Field(default=None, description="릴리즈 시각")


class DrawingCreate(BaseModel):
    """도면 생성 요청 스키마."""

    drawing_number: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    drawing_type: DrawingType
    product_id: str | None = None
    file_url: str
    file_name: str
    file_size: int
    file_format: str
    thumbnail_url: str | None = None
    linked_bom_items: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class DrawingUpdate(BaseModel):
    """도면 수정 요청 스키마."""

    title: str | None = None
    drawing_type: DrawingType | None = None
    product_id: str | None = None
    thumbnail_url: str | None = None
    linked_bom_items: list[str] | None = None
    tags: list[str] | None = None


class Drawing(BaseDocument):
    """도면 문서 — 엔지니어링 문서를 버전 관리.

    naming prefix: DWG
    """

    drawing_number: str = Field(default="", description="도면 번호")
    title: str = Field(default="", description="도면 제목")
    drawing_type: DrawingType = Field(default=DrawingType.PART_DRAWING, description="도면 유형")
    product_id: str | None = Field(default=None, description="관련 제품")
    revision: str = Field(default="A", description="현재 리비전")
    revision_history: list[RevisionEntry] = Field(default_factory=list, description="리비전 이력")
    status: DrawingStatus = Field(default=DrawingStatus.WORK_IN_PROGRESS, description="���태")
    file_url: str = Field(default="", description="원본 파일 URL")
    file_name: str = Field(default="", description="파일명")
    file_size: int = Field(default=0, description="파일 크기(bytes)")
    file_format: str = Field(default="", description="파일 형식")
    thumbnail_url: str | None = Field(default=None, description="썸네일 이미지 URL")
    checked_out_by: str | None = Field(default=None, description="체크아웃 사용자")
    checked_out_at: datetime | None = Field(default=None, description="체크아��� 시각")
    linked_bom_items: list[str] = Field(default_factory=list, description="연결된 BOM 부품")
    linked_eco_ids: list[str] = Field(default_factory=list, description="관련 ECO")
    tags: list[str] = Field(default_factory=list, description="검색 태그")
    deleted_at: str | None = Field(default=None, description="삭제 시각")
