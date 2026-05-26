"""점검결과(InspectionResult) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class InspectionOutcome(StrEnum):
    """점검 결과."""

    PASS = "pass"  # noqa: S105
    FAIL = "fail"
    CONDITIONAL = "conditional"


class InspectionItemResult(BaseModel):
    """개별 점검 항목 결과."""

    idx: int = 0
    item_name: str = ""
    outcome: InspectionOutcome = InspectionOutcome.PASS
    measured_value: str = ""
    remarks: str = ""


class InspectionResultCreate(BaseModel):
    """점검결과 생성 요청 스키마."""

    checklist_id: str
    equipment_id: str
    inspection_date: date | None = None
    inspector: str = ""
    item_results: list[InspectionItemResult] = Field(default_factory=list)
    overall_outcome: InspectionOutcome = InspectionOutcome.PASS
    remarks: str = ""


class InspectionResultUpdate(BaseModel):
    """점검결과 수정 요청 스키마."""

    checklist_id: str | None = None
    equipment_id: str | None = None
    inspection_date: date | None = None
    inspector: str | None = None
    item_results: list[InspectionItemResult] | None = None
    overall_outcome: InspectionOutcome | None = None
    remarks: str | None = None


class InspectionResult(BaseDocument):
    """점검결과 문서."""

    checklist_id: str = ""
    equipment_id: str = ""
    inspection_date: date | None = None
    inspector: str = ""
    item_results: list[InspectionItemResult] = Field(default_factory=list)
    overall_outcome: InspectionOutcome = InspectionOutcome.PASS
    remarks: str = ""
