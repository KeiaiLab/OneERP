"""검사결과(InspectionResult) 문서 모델 — Quality 모듈 (Log)."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class InspectionResultCreate(BaseModel):
    """검사결과 생성 요청 스키마."""

    inspection_id: str
    parameter: str = ""
    result: str = ""
    status: str = "pass"
    remarks: str = ""


class InspectionResult(BaseDocument):
    """검사결과 문서 — Quality 검사결과 로그.

    naming prefix: INSR
    """

    inspection_id: str = ""
    parameter: str = ""
    result: str = ""
    status: str = "pass"
    remarks: str = ""
