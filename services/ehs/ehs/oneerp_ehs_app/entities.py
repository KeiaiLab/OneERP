"""EHS 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

4개 엔티티를 EntityMeta로 선언한다.
사고 통계 보고서는 routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.hazardous_material import (
    HazardousMaterial,
    HazardousMaterialCreate,
    HazardousMaterialUpdate,
)
from .models.health_checkup import (
    HealthCheckup,
    HealthCheckupCreate,
    HealthCheckupUpdate,
)
from .models.safety_incident import (
    SafetyIncident,
    SafetyIncidentCreate,
    SafetyIncidentUpdate,
)
from .models.safety_training import (
    SafetyTraining,
    SafetyTrainingCreate,
    SafetyTrainingUpdate,
)

# --- 마스터 데이터 ---

HAZARDOUS_MATERIAL = EntityMeta(
    collection="hazardous_materials",
    prefix="HM",
    api_path="/api/v1/hazardous-materials",
    tag="위험물",
    resource="hazardous_material",
    model=HazardousMaterial,
    create_schema=HazardousMaterialCreate,
    update_schema=HazardousMaterialUpdate,
    archetype="master",
    not_found_message="위험물을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

SAFETY_INCIDENT = EntityMeta(
    collection="safety_incidents",
    prefix="SI",
    api_path="/api/v1/safety-incidents",
    tag="안전 사고",
    resource="safety_incident",
    model=SafetyIncident,
    create_schema=SafetyIncidentCreate,
    update_schema=SafetyIncidentUpdate,
    archetype="transaction",
    not_found_message="안전 사고를 찾을 수 없습니다",
)

SAFETY_TRAINING = EntityMeta(
    collection="safety_trainings",
    prefix="ST",
    api_path="/api/v1/safety-trainings",
    tag="안전 교육",
    resource="safety_training",
    model=SafetyTraining,
    create_schema=SafetyTrainingCreate,
    update_schema=SafetyTrainingUpdate,
    archetype="transaction",
    not_found_message="안전 교육을 찾을 수 없습니다",
)

HEALTH_CHECKUP = EntityMeta(
    collection="health_checkups",
    prefix="HC",
    api_path="/api/v1/health-checkups",
    tag="건강검진",
    resource="health_checkup",
    model=HealthCheckup,
    create_schema=HealthCheckupCreate,
    update_schema=HealthCheckupUpdate,
    archetype="transaction",
    not_found_message="건강검진을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    HAZARDOUS_MATERIAL,
    # 트랜잭션
    SAFETY_INCIDENT,
    SAFETY_TRAINING,
    HEALTH_CHECKUP,
]
