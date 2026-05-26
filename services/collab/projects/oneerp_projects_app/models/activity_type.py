"""활동유형(ActivityType) 문서 모델 — Projects 모듈.

L2 비즈니스 룰: BR-PROJ-008 (활동유형 단가 양수).
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ActivityTypeCreate(BaseModel):
    """활동유형 생성 요청 스키마."""

    activity_type: str
    costing_rate: Decimal = Decimal(0)
    billing_rate: Decimal = Decimal(0)


class ActivityTypeUpdate(BaseModel):
    """활동유형 수정 요청 스키마."""

    activity_type: str | None = None
    costing_rate: Decimal | None = None
    billing_rate: Decimal | None = None


class ActivityType(BaseDocument):
    """활동유형 문서 — Projects 활동유형 마스터.

    naming prefix: ATYP
    """

    activity_type: str = ""
    costing_rate: Decimal = Decimal(0)
    billing_rate: Decimal = Decimal(0)
