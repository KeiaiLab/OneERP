"""영업구역(Territory) 마스터 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from oneerp_core.models import BaseTerritoryFields
from pydantic import BaseModel


class TerritoryCreate(BaseTerritoryFields):
    """영업구역 생성 요청 스키마."""

    parent_territory: str | None = None
    territory_manager: str = ""


class TerritoryUpdate(BaseModel):
    """영업구역 수정 요청 스키마."""

    territory_name: str | None = None
    parent_territory: str | None = None
    territory_manager: str | None = None


class Territory(BaseDocument, BaseTerritoryFields):
    """영업구역 마스터 — 판매 영역 관리.

    naming prefix: TER
    """

    parent_territory: str | None = None
    territory_manager: str = ""
