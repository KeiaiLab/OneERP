"""Projects 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

7개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 엔티티(프로젝트, 태스크, 타임시트 등)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.project_billing import (
    ProjectBilling,
    ProjectBillingCreate,
    ProjectBillingUpdate,
)
from .models.project_revenue_recognition import (
    ProjectRevenueRecognition,
    ProjectRevenueRecognitionCreate,
    ProjectRevenueRecognitionUpdate,
)
from .models.project_risk import ProjectRisk, ProjectRiskCreate, ProjectRiskUpdate
from .models.project_template import (
    ProjectTemplate,
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
)
from .models.resource_allocation import (
    ResourceAllocation,
    ResourceAllocationCreate,
    ResourceAllocationUpdate,
)
from .models.task_template import TaskTemplate, TaskTemplateCreate, TaskTemplateUpdate
from .models.wbs_element import WbsElement, WbsElementCreate, WbsElementUpdate

# --- 마스터 데이터 ---

PROJECT_TEMPLATE = EntityMeta(
    collection="project_templates",
    prefix="PTPL",
    api_path="/api/v1/project-templates",
    tag="프로젝트템플릿",
    resource="project_template",
    model=ProjectTemplate,
    create_schema=ProjectTemplateCreate,
    update_schema=ProjectTemplateUpdate,
    archetype="master",
    not_found_message="프로젝트 템플릿을 찾을 수 없습니다",
)

TASK_TEMPLATE = EntityMeta(
    collection="task_templates",
    prefix="TTPL",
    api_path="/api/v1/task-templates",
    tag="태스크템플릿",
    resource="task_template",
    model=TaskTemplate,
    create_schema=TaskTemplateCreate,
    update_schema=TaskTemplateUpdate,
    archetype="master",
    not_found_message="태스크 템플릿을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

RESOURCE_ALLOCATION = EntityMeta(
    collection="resource_allocations",
    prefix="RALL",
    api_path="/api/v1/resource-allocations",
    tag="자원할당",
    resource="resource_allocation",
    model=ResourceAllocation,
    create_schema=ResourceAllocationCreate,
    update_schema=ResourceAllocationUpdate,
    archetype="transaction",
    not_found_message="자원 할당을 찾을 수 없습니다",
)

PROJECT_BILLING = EntityMeta(
    collection="project_billings",
    prefix="PBIL",
    api_path="/api/v1/project-billings",
    tag="프로젝트청구",
    resource="project_billing",
    model=ProjectBilling,
    create_schema=ProjectBillingCreate,
    update_schema=ProjectBillingUpdate,
    archetype="transaction",
    not_found_message="프로젝트 청구를 찾을 수 없습니다",
)

WBS_ELEMENT = EntityMeta(
    collection="wbs_elements",
    prefix="WBS",
    api_path="/api/v1/wbs-elements",
    tag="WBS요소",
    resource="wbs_element",
    model=WbsElement,
    create_schema=WbsElementCreate,
    update_schema=WbsElementUpdate,
    archetype="master",
    not_found_message="WBS 요소를 찾을 수 없습니다",
)

PROJECT_RISK = EntityMeta(
    collection="project_risks",
    prefix="PRSK",
    api_path="/api/v1/project-risks",
    tag="프로젝트리스크",
    resource="project_risk",
    model=ProjectRisk,
    create_schema=ProjectRiskCreate,
    update_schema=ProjectRiskUpdate,
    archetype="transaction",
    not_found_message="프로젝트 리스크를 찾을 수 없습니다",
)

PROJECT_REVENUE_RECOGNITION = EntityMeta(
    collection="project_revenue_recognitions",
    prefix="PRREC",
    api_path="/api/v1/project-revenue-recognitions",
    tag="프로젝트수익인식",
    resource="project_revenue_recognition",
    model=ProjectRevenueRecognition,
    create_schema=ProjectRevenueRecognitionCreate,
    update_schema=ProjectRevenueRecognitionUpdate,
    archetype="transaction",
    not_found_message="프로젝트 수익 인식을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    PROJECT_TEMPLATE,
    TASK_TEMPLATE,
    WBS_ELEMENT,
    # 트랜잭션
    RESOURCE_ALLOCATION,
    PROJECT_BILLING,
    PROJECT_RISK,
    PROJECT_REVENUE_RECOGNITION,
]
