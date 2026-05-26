"""고급계획 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용."""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.capacity_plan import CapacityPlan, CapacityPlanCreate, CapacityPlanUpdate
from .models.demand_plan import DemandPlan, DemandPlanCreate, DemandPlanUpdate
from .models.planning_scenario import (
    PlanningScenario,
    PlanningScenarioCreate,
    PlanningScenarioUpdate,
)
from .models.scheduling_rule import SchedulingRule, SchedulingRuleCreate, SchedulingRuleUpdate
from .models.supply_plan import SupplyPlan, SupplyPlanCreate, SupplyPlanUpdate

ENTITY_METAS: list[EntityMeta] = [
    EntityMeta(
        collection="demand_plans",
        prefix="DMP",
        api_path="/api/v1/planning/demand-plans",
        tag="수요계획",
        resource="demand_plan",
        model=DemandPlan,
        create_schema=DemandPlanCreate,
        update_schema=DemandPlanUpdate,
        archetype="transaction",
        not_found_message="수요계획을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="supply_plans",
        prefix="SPP",
        api_path="/api/v1/planning/supply-plans",
        tag="공급계획",
        resource="supply_plan",
        model=SupplyPlan,
        create_schema=SupplyPlanCreate,
        update_schema=SupplyPlanUpdate,
        archetype="transaction",
        not_found_message="공급계획을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="capacity_plans",
        prefix="CPP",
        api_path="/api/v1/planning/capacity-plans",
        tag="생산능력계획",
        resource="capacity_plan",
        model=CapacityPlan,
        create_schema=CapacityPlanCreate,
        update_schema=CapacityPlanUpdate,
        archetype="transaction",
        not_found_message="생산능력계획을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="scheduling_rules",
        prefix="SCR",
        api_path="/api/v1/planning/scheduling-rules",
        tag="스케줄링규칙",
        resource="scheduling_rule",
        model=SchedulingRule,
        create_schema=SchedulingRuleCreate,
        update_schema=SchedulingRuleUpdate,
        archetype="master",
        not_found_message="스케줄링 규칙을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="planning_scenarios",
        prefix="PLS",
        api_path="/api/v1/planning/scenarios",
        tag="계획시나리오",
        resource="planning_scenario",
        model=PlanningScenario,
        create_schema=PlanningScenarioCreate,
        update_schema=PlanningScenarioUpdate,
        archetype="transaction",
        not_found_message="계획 시나리오를 찾을 수 없습니다",
    ),
]
