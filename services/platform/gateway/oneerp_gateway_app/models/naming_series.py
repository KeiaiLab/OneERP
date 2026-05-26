"""채번규칙(NamingSeries) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class NamingSeriesCreate(BaseModel):
    """채번규칙 생성 요청 스키마."""

    prefix: str
    current_value: int = 0
    description: str = ""


class NamingSeriesUpdate(BaseModel):
    """채번규칙 수정 요청 스키마."""

    prefix: str | None = None
    current_value: int | None = None
    description: str | None = None


class NamingSeries(BaseDocument):
    """채번규칙 문서 — Setup 채번규칙 마스터.

    naming prefix: NSRS
    """

    prefix: str = ""
    current_value: int = 0
    description: str = ""
