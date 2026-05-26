"""영역 관리(TerritoryManagement) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from oneerp_core.models import BaseTerritoryFields
from pydantic import BaseModel


class TerritoryManagementCreate(BaseTerritoryFields):
    """영역 관리 생성 요청 스키마."""

    manager_id: str = ""
    region: str = ""
    customer_count: int = 0
    target_revenue: Decimal = Decimal(0)
    territory_ref: str = ""


class TerritoryManagementUpdate(BaseModel):
    """영역 관리 수정 요청 스키마."""

    territory_name: str | None = None
    manager_id: str | None = None
    region: str | None = None
    customer_count: int | None = None
    target_revenue: Decimal | None = None
    territory_ref: str | None = None


class TerritoryManagement(BaseDocument, BaseTerritoryFields):
    """영역 관리 문서."""

    manager_id: str = ""
    region: str = ""
    customer_count: int = 0
    target_revenue: Decimal = Decimal(0)
    territory_ref: str = ""
