"""Reservation 서비스 엔티티 메타 선언.

3개 엔티티 (Resource, Reservation, ReservationPolicy)를 EntityMeta로 선언한다.
모든 엔티티는 커스텀 라우터를 사용하므로 ENTITY_METAS는 빈 목록이다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.reservation import (
    Reservation,
    ReservationCreate,
    ReservationUpdate,
)
from .models.reservation_policy import (
    ReservationPolicy,
    ReservationPolicyCreate,
    ReservationPolicyUpdate,
)
from .models.resource import (
    Resource,
    ResourceCreate,
    ResourceUpdate,
)

# --- 마스터 데이터 ---

RESOURCE = EntityMeta(
    collection="resources",
    prefix="RSC",
    api_path="/api/v1/resources",
    tag="자원",
    resource="resource",
    model=Resource,
    create_schema=ResourceCreate,
    update_schema=ResourceUpdate,
    archetype="master",
    not_found_message="자원을 찾을 수 없습니다",
)

RESERVATION_POLICY = EntityMeta(
    collection="reservation_policies",
    prefix="RPL",
    api_path="/api/v1/reservation-policies",
    tag="예약정책",
    resource="reservation_policy",
    model=ReservationPolicy,
    create_schema=ReservationPolicyCreate,
    update_schema=ReservationPolicyUpdate,
    archetype="master",
    not_found_message="예약 정책을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

RESERVATION = EntityMeta(
    collection="reservations",
    prefix="RSV",
    api_path="/api/v1/reservations",
    tag="예약",
    resource="reservation",
    model=Reservation,
    create_schema=ReservationCreate,
    update_schema=ReservationUpdate,
    archetype="transaction",
    not_found_message="예약을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
# — 모든 엔티티가 커스텀 라우터(extra_routers)를 사용하므로
#   자동 CRUD 생성 대상은 없다.
ENTITY_METAS: list[EntityMeta] = []
