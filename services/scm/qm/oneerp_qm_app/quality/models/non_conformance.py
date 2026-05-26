"""부적합(NonConformance) 문서 모델 — Quality 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class NonConformanceCreate(BaseModel):
    """부적합 생성 요청 스키마."""

    title: str
    description: str = ""
    severity: str = "minor"
    item_code: str = ""
    inspection_id: str = ""
    corrective_action: str = ""


class NonConformanceUpdate(BaseModel):
    """부적합 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    severity: str | None = None
    item_code: str | None = None
    inspection_id: str | None = None
    corrective_action: str | None = None


class NonConformance(BaseDocument):
    """부적합 문서 — Quality 부적합 트랜잭션.

    naming prefix: NC
    """

    title: str = ""
    description: str = ""
    severity: str = "minor"
    item_code: str = ""
    inspection_id: str = ""
    corrective_action: str = ""
