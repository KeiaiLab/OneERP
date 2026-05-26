"""프로젝트 수익 인식(ProjectRevenueRecognition) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ProjectRevenueRecognitionCreate(BaseModel):
    """프로젝트 수익 인식 생성 요청 스키마."""

    project_id: str
    recognition_date: date | None = None
    recognized_amount: Decimal = Decimal(0)
    total_contract_value: Decimal = Decimal(0)
    completion_percentage: Decimal = Decimal(0)


class ProjectRevenueRecognitionUpdate(BaseModel):
    """프로젝트 수익 인식 수정 요청 스키마."""

    project_id: str | None = None
    recognition_date: date | None = None
    recognized_amount: Decimal | None = None
    total_contract_value: Decimal | None = None
    completion_percentage: Decimal | None = None


class ProjectRevenueRecognition(BaseDocument):
    """프로젝트 수익 인식 문서."""

    project_id: str = ""
    recognition_date: date | None = None
    recognized_amount: Decimal = Decimal(0)
    total_contract_value: Decimal = Decimal(0)
    completion_percentage: Decimal = Decimal(0)
