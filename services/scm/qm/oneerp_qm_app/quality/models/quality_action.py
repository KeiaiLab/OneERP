"""품질 조치(QualityAction) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class QualityActionCreate(BaseModel):
    """품질 조치 생성 요청 스키마."""

    action_name: str
    action_type: str = ""
    responsible: str = ""
    due_date: date | None = None
    is_completed: bool = False


class QualityActionUpdate(BaseModel):
    """품질 조치 수정 요청 스키마."""

    action_name: str | None = None
    action_type: str | None = None
    responsible: str | None = None
    due_date: date | None = None
    is_completed: bool | None = None


class QualityAction(BaseDocument):
    """품질 조치 문서."""

    action_name: str = ""
    action_type: str = ""
    responsible: str = ""
    due_date: date | None = None
    is_completed: bool = False
