"""KPI 정의(KPIDefinition) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class KPIDefinitionCreate(BaseModel):
    """KPI 정의 생성 요청 스키마."""

    kpi_name: str
    description: str = ""
    formula: str = ""
    unit: str = ""
    target_value: Decimal = Decimal(0)
    is_active: bool = True


class KPIDefinitionUpdate(BaseModel):
    """KPI 정의 수정 요청 스키마."""

    kpi_name: str | None = None
    description: str | None = None
    formula: str | None = None
    unit: str | None = None
    target_value: Decimal | None = None
    is_active: bool | None = None


class KPIDefinition(BaseDocument):
    """KPI 정의 문서."""

    kpi_name: str = ""
    description: str = ""
    formula: str = ""
    unit: str = ""
    target_value: Decimal = Decimal(0)
    is_active: bool = True
