"""품질검사(QualityInspection) 모델 정의."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class InspectionReferenceType(StrEnum):
    """검사 참조 문서 유형."""

    PURCHASE_RECEIPT = "purchase_receipt"
    STOCK_ENTRY = "stock_entry"


class InspectionType(StrEnum):
    """검사 유형."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"
    IN_PROCESS = "in_process"


class ReadingStatus(StrEnum):
    """측정 결과 상태."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"


class QualityReading(LineItem):
    """품질 측정 라인 — 검사 항목별 측정값."""

    parameter: str
    specification: str = ""
    reading: str = ""
    status: ReadingStatus = ReadingStatus.ACCEPTED


class QualityInspection(BaseDocument):
    """품질검사 문서 — 입고/출고/공정 중 품질 검사.

    naming prefix: QI
    """

    reference_type: InspectionReferenceType
    reference_no: str
    inspection_type: InspectionType
    item_code: str
    readings: list[QualityReading] = []
    result: ReadingStatus = ReadingStatus.ACCEPTED


class QualityInspectionCreate(BaseModel):
    """품질검사 생성 요청 스키마."""

    reference_type: InspectionReferenceType
    reference_no: str
    inspection_type: InspectionType
    item_code: str
    readings: list[QualityReading] = []
    result: ReadingStatus = ReadingStatus.ACCEPTED


class QualityInspectionUpdate(BaseModel):
    """품질검사 수정 요청 스키마 — 모든 필드 선택적."""

    reference_type: InspectionReferenceType | None = None
    reference_no: str | None = None
    inspection_type: InspectionType | None = None
    item_code: str | None = None
    readings: list[QualityReading] | None = None
    result: ReadingStatus | None = None
