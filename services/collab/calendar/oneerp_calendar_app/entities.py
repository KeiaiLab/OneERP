"""Calendar 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

7개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 3개 엔티티(calendar_events, resource_bookings, holidays)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.calendar import Calendar, CalendarCreate, CalendarUpdate
from .models.invitee import Invitee, InviteeCreate, InviteeUpdate
from .models.reminder import Reminder, ReminderCreate, ReminderUpdate
from .models.resource import Resource, ResourceCreate, ResourceUpdate

# --- 마스터 데이터 ---

CALENDAR = EntityMeta(
    collection="calendars",
    prefix="CAL",
    api_path="/api/v1/calendars",
    tag="캘린더",
    resource="calendar",
    model=Calendar,
    create_schema=CalendarCreate,
    update_schema=CalendarUpdate,
    archetype="master",
    not_found_message="캘린더를 찾을 수 없습니다",
)

RESOURCE = EntityMeta(
    collection="resources",
    prefix="CRES",
    api_path="/api/v1/resources",
    tag="자원",
    resource="resource",
    model=Resource,
    create_schema=ResourceCreate,
    update_schema=ResourceUpdate,
    archetype="master",
    not_found_message="자원을 찾을 수 없습니다",
)

INVITEE = EntityMeta(
    collection="invitees",
    prefix="CINV",
    api_path="/api/v1/invitees",
    tag="초대자",
    resource="invitee",
    model=Invitee,
    create_schema=InviteeCreate,
    update_schema=InviteeUpdate,
    archetype="master",
    not_found_message="초대자를 찾을 수 없습니다",
)

REMINDER = EntityMeta(
    collection="reminders",
    prefix="CREM",
    api_path="/api/v1/reminders",
    tag="리마인더",
    resource="reminder",
    model=Reminder,
    create_schema=ReminderCreate,
    update_schema=ReminderUpdate,
    archetype="master",
    not_found_message="리마인더를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    CALENDAR,
    RESOURCE,
    INVITEE,
    REMINDER,
]
