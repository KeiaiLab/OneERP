"""계획 시나리오 모델 — What-if 분석을 위한 계획 시나리오를 관리한다."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PlanningScenarioCreate(BaseModel):
    """계획 시나리오 생성 요청 스키마."""

    scenario_name: str
    scenario_type: str = "what_if"  # what_if/baseline/optimistic/pessimistic
    base_demand_plan_id: str = ""
    assumptions: dict = {}
    demand_adjustment: Decimal = Decimal(0)  # 수요 조정 비율 (%)
    description: str = ""


class PlanningScenarioUpdate(BaseModel):
    """계획 시나리오 수정 요청 스키마."""

    scenario_name: str | None = None
    assumptions: dict | None = None
    demand_adjustment: Decimal | None = None
    results: dict | None = None
    status: str | None = None
    description: str | None = None


class PlanningScenario(BaseDocument):
    """계획 시나리오 문서 — What-if 분석 시나리오를 저장한다."""

    scenario_name: str = ""
    scenario_type: str = "what_if"
    base_demand_plan_id: str = ""
    assumptions: dict = {}
    demand_adjustment: Decimal = Decimal(0)
    results: dict = {}  # total_cost, service_level, inventory_level 등
    status: str = "draft"  # draft/running/completed
    description: str = ""
