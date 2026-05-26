"""시정예방조치(Capa) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CapaCreate(BaseModel):
    """시정예방조치 생성 요청 스키마."""

    capa_type: str
    problem_description: str = ""
    root_cause: str = ""
    corrective_action: str = ""
    responsible: str = ""
    due_date: date | None = None
    is_closed: bool = False


class CapaUpdate(BaseModel):
    """시정예방조치 수정 요청 스키마."""

    capa_type: str | None = None
    problem_description: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    responsible: str | None = None
    due_date: date | None = None
    is_closed: bool | None = None


class Capa(BaseDocument):
    """시정예방조치 문서."""

    capa_type: str = ""
    problem_description: str = ""
    root_cause: str = ""
    corrective_action: str = ""
    responsible: str = ""
    due_date: date | None = None
    is_closed: bool = False
