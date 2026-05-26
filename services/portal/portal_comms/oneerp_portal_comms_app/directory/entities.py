"""조직도/인명부 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

5개 엔티티를 EntityMeta로 선언한다.
커스텀 로직은 routes/ 및 services/ 디렉토리에서 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.employee_directory import (
    EmployeeDirectory,
    EmployeeDirectoryCreate,
    EmployeeDirectoryUpdate,
)
from .models.org_chart_snapshot import (
    OrgChartSnapshot,
    OrgChartSnapshotCreate,
    OrgChartSnapshotUpdate,
)
from .models.org_unit import OrgUnit, OrgUnitCreate, OrgUnitUpdate
from .models.organization import Organization, OrganizationCreate, OrganizationUpdate
from .models.position import Position, PositionCreate, PositionUpdate

# --- 마스터 데이터 ---

ORGANIZATION = EntityMeta(
    collection="organizations",
    prefix="ORG",
    api_path="/api/v1/organizations",
    tag="조직",
    resource="organization",
    model=Organization,
    create_schema=OrganizationCreate,
    update_schema=OrganizationUpdate,
    archetype="master",
    not_found_message="조직을 찾을 수 없습니다",
)

ORG_UNIT = EntityMeta(
    collection="org_units",
    prefix="UNIT",
    api_path="/api/v1/org-units",
    tag="조직단위",
    resource="org_unit",
    model=OrgUnit,
    create_schema=OrgUnitCreate,
    update_schema=OrgUnitUpdate,
    archetype="master",
    not_found_message="조직 단위를 찾을 수 없습니다",
)

POSITION = EntityMeta(
    collection="positions",
    prefix="POS",
    api_path="/api/v1/positions",
    tag="직위",
    resource="position",
    model=Position,
    create_schema=PositionCreate,
    update_schema=PositionUpdate,
    archetype="master",
    not_found_message="직위를 찾을 수 없습니다",
)

# --- 트랜잭션 데이터 ---

EMPLOYEE_DIRECTORY = EntityMeta(
    collection="employee_directories",
    prefix="EDIR",
    api_path="/api/v1/employee-directories",
    tag="인명부",
    resource="employee_directory",
    model=EmployeeDirectory,
    create_schema=EmployeeDirectoryCreate,
    update_schema=EmployeeDirectoryUpdate,
    archetype="transaction",
    not_found_message="인명부 엔트리를 찾을 수 없습니다",
)

ORG_CHART_SNAPSHOT = EntityMeta(
    collection="org_chart_snapshots",
    prefix="SNAP",
    api_path="/api/v1/org-chart-snapshots",
    tag="조직도스냅샷",
    resource="org_chart_snapshot",
    model=OrgChartSnapshot,
    create_schema=OrgChartSnapshotCreate,
    update_schema=OrgChartSnapshotUpdate,
    archetype="transaction",
    not_found_message="조직도 스냅샷을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    ORGANIZATION,
    ORG_UNIT,
    POSITION,
    # 트랜잭션
    EMPLOYEE_DIRECTORY,
    ORG_CHART_SNAPSHOT,
]
