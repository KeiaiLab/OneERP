"""품질검사템플릿(QualityInspectionTemplate) 문서 모델 — Quality 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class QualityInspectionTemplateCreate(BaseModel):
    """품질검사템플릿 생성 요청 스키마."""

    template_name: str
    inspection_type: str = "incoming"
    parameters: str = ""


class QualityInspectionTemplateUpdate(BaseModel):
    """품질검사템플릿 수정 요청 스키마."""

    template_name: str | None = None
    inspection_type: str | None = None
    parameters: str | None = None


class QualityInspectionTemplate(BaseDocument):
    """품질검사템플릿 문서 — Quality 검사템플릿 마스터.

    naming prefix: QITM
    """

    template_name: str = ""
    inspection_type: str = "incoming"
    parameters: str = ""
