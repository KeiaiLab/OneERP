"""품질목표(QualityGoal) 문서 모델 — Quality 모듈."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class QualityGoalCreate(BaseModel):
    """품질목표 생성 요청 스키마."""

    goal_name: str
    target_value: Decimal = Decimal(0)
    current_value: Decimal = Decimal(0)
    unit: str = ""
    period: str = ""
    status: str = "in_progress"


class QualityGoalUpdate(BaseModel):
    """품질목표 수정 요청 스키마."""

    goal_name: str | None = None
    target_value: Decimal | None = None
    current_value: Decimal | None = None
    unit: str | None = None
    period: str | None = None
    status: str | None = None


class QualityGoal(BaseDocument):
    """품질목표 문서 — Quality 품질목표 마스터.

    naming prefix: QGOL
    """

    goal_name: str = ""
    target_value: Decimal = Decimal(0)
    current_value: Decimal = Decimal(0)
    unit: str = ""
    period: str = ""
    status: str = "in_progress"
