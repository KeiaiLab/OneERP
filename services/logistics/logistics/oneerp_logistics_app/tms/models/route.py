"""배송 경로(Route) 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class Location(BaseModel):
    """위치 정보."""

    name: str = ""
    address: str = ""
    lat: float | None = None
    lng: float | None = None


class Waypoint(BaseModel):
    """경유지 정보."""

    name: str = ""
    address: str = ""
    lat: float | None = None
    lng: float | None = None
    stop_minutes: int = 0


class RouteCreate(BaseModel):
    """배송 경로 생성 요청."""

    route_name: str
    origin: Location
    destination: Location
    waypoints: list[Waypoint] | None = None
    distance_km: float | None = None
    estimated_minutes: int | None = None
    preferred_carrier_id: str | None = None
    preferred_vehicle_type: str | None = None
    region_group: str | None = None
    is_active: bool = True
    company: str = ""


class RouteUpdate(BaseModel):
    """배송 경로 수정 요청."""

    route_name: str | None = None
    origin: Location | None = None
    destination: Location | None = None
    waypoints: list[Waypoint] | None = None
    distance_km: float | None = None
    estimated_minutes: int | None = None
    preferred_carrier_id: str | None = None
    preferred_vehicle_type: str | None = None
    region_group: str | None = None
    is_active: bool | None = None
    company: str | None = None


class Route(BaseDocument):
    """배송 경로 마스터 — 반복 사용 배송 경로 정보.

    naming prefix: RTE
    """

    route_name: str = Field(default="", description="경로명")
    origin: Location = Field(default_factory=Location, description="출발지")
    destination: Location = Field(default_factory=Location, description="도착��")
    waypoints: list[Waypoint] = Field(default_factory=list, description="경유지 목록")
    distance_km: float | None = Field(default=None, description="총 거리 (km)")
    estimated_minutes: int | None = Field(default=None, description="예상 소요 시간 (분)")
    preferred_carrier_id: str | None = Field(default=None, description="선호 운송사")
    preferred_vehicle_type: str | None = Field(default=None, description="선호 차량 유형")
    region_group: str | None = Field(default=None, description="지역 그룹")
    is_active: bool = Field(default=True, description="활성 여부")
    company: str = Field(default="", description="회사")
