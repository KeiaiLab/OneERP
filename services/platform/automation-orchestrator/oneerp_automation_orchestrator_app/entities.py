"""automation-orchestrator 서비스 엔티티 메타 선언."""

from __future__ import annotations

from typing import Any, cast

from oneerp_core.entity_meta import EntityMeta

AUTOMATION_DEFINITION = EntityMeta(
    collection="automation_definitions",
    prefix="ADEF",
    api_path="/api/v1/automation-definitions",
    tag="자동화 정의",
    resource="automation_definition",
    model=cast("type[Any]", object),
    create_schema=cast("type[Any]", object),
    update_schema=cast("type[Any]", object),
    archetype="master",
    not_found_message="자동화 정의를 찾을 수 없습니다",
)

AUTOMATION_TRIGGER = EntityMeta(
    collection="automation_triggers",
    prefix="ATRG",
    api_path="/api/v1/automation-triggers",
    tag="자동화 트리거",
    resource="automation_trigger",
    model=cast("type[Any]", object),
    create_schema=cast("type[Any]", object),
    update_schema=cast("type[Any]", object),
    archetype="master",
    not_found_message="자동화 트리거를 찾을 수 없습니다",
)

AUTOMATION_SCHEDULE = EntityMeta(
    collection="automation_schedules",
    prefix="ASCH",
    api_path="/api/v1/automation-schedules",
    tag="자동화 스케줄",
    resource="automation_schedule",
    model=cast("type[Any]", object),
    create_schema=cast("type[Any]", object),
    update_schema=cast("type[Any]", object),
    archetype="master",
    not_found_message="자동화 스케줄을 찾을 수 없습니다",
)

AUTOMATION_RUN = EntityMeta(
    collection="automation_runs",
    prefix="ARUN",
    api_path="/api/v1/automation-runs",
    tag="자동화 실행",
    resource="automation_run",
    model=cast("type[Any]", object),
    create_schema=cast("type[Any]", object),
    update_schema=cast("type[Any]", object),
    archetype="transaction",
    not_found_message="자동화 실행을 찾을 수 없습니다",
)

HUMAN_TASK = EntityMeta(
    collection="human_tasks",
    prefix="HTSK",
    api_path="/api/v1/human-tasks",
    tag="휴먼 태스크",
    resource="human_task",
    model=cast("type[Any]", object),
    create_schema=cast("type[Any]", object),
    update_schema=cast("type[Any]", object),
    archetype="transaction",
    not_found_message="휴먼 태스크를 찾을 수 없습니다",
)

ENTITY_METAS: list[EntityMeta] = []
