"""설계 변경 통보(ECN) 문서 모델.

ECO 승인 후 변경 내용을 관련 부서에 공식 통보하는 문서.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class ECNStatus(StrEnum):
    """ECN 상태."""

    ISSUED = "issued"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BOMChange(BaseModel):
    """BOM 변경 — 임베디드 모델."""

    bom_version_from: str = Field(description="변경 전 BOM 버전 ID")
    bom_version_to: str = Field(description="변경 후 BOM 버전 ID")
    change_summary: str = Field(default="", description="변경 요약")


class DrawingChange(BaseModel):
    """도면 변경 — 임베디드 모델."""

    drawing_id: str = Field(description="도면 ID")
    revision_from: str = Field(description="변경 전 리비전")
    revision_to: str = Field(description="변경 후 리비전")
    change_summary: str = Field(default="", description="변경 요약")


class Acknowledgement(BaseModel):
    """수신 확인 — 임베디드 모델."""

    user_id: str = Field(description="수신자 ID")
    user_name: str = Field(default="", description="수신자명")
    acknowledged: bool = Field(default=False, description="확인 여부")
    acknowledged_at: datetime | None = Field(default=None, description="확인 시각")


class ECNCreate(BaseModel):
    """ECN 생성 요청 스키마."""

    eco_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str
    effective_date: date
    effectivity_type: str = "date"
    effectivity_value: str | None = None
    bom_changes: list[BOMChange] = Field(default_factory=list)
    drawing_changes: list[DrawingChange] = Field(default_factory=list)
    distribution_list: list[str] = Field(min_length=1)
    issued_by: str = ""


class ECNUpdate(BaseModel):
    """ECN 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    effective_date: date | None = None


class EngChangeNotice(BaseDocument):
    """설계 변경 통보 문서 — ECN.

    naming prefix: ECN
    """

    ecn_number: str = Field(default="", description="ECN 번호")
    eco_id: str = Field(default="", description="원본 ECO")
    title: str = Field(default="", description="변경 통보 제목")
    description: str = Field(default="", description="변경 내용 상세")
    status: ECNStatus = Field(default=ECNStatus.ISSUED, description="상태")
    effective_date: date | None = Field(default=None, description="변경 적용일")
    effectivity_type: str = Field(default="date", description="유효성 기준 유��")
    effectivity_value: str | None = Field(default=None, description="유효성 기준 값")
    bom_changes: list[BOMChange] = Field(default_factory=list, description="BOM 변경 목록")
    drawing_changes: list[DrawingChange] = Field(default_factory=list, description="도면 변경 목록")
    distribution_list: list[str] = Field(default_factory=list, description="배포 대상")
    acknowledgements: list[Acknowledgement] = Field(default_factory=list, description="수신 확인")
    issued_by: str = Field(default="", description="발행자")
    issued_at: datetime | None = Field(default=None, description="발행 시각")
    completed_at: datetime | None = Field(default=None, description="���료 시각")
