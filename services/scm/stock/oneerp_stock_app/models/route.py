"""운송 경로(Route) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RouteCreate(BaseModel):
    """운송 경로 생성 요청 스키마."""

    route_name: str
    origin: str = ""
    destination: str = ""
    estimated_days: int = 0
    carrier_id: str = ""


class RouteUpdate(BaseModel):
    """운송 경로 수정 요청 스키마."""

    route_name: str | None = None
    origin: str | None = None
    destination: str | None = None
    estimated_days: int | None = None
    carrier_id: str | None = None


class Route(BaseDocument):
    """운송 경로 문서."""

    route_name: str = ""
    origin: str = ""
    destination: str = ""
    estimated_days: int = 0
    carrier_id: str = ""
