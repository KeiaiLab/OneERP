"""Compliance 클러스터 FastAPI 앱 — compliance + clm 통합 진입점."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .clm.entities import ENTITY_METAS as CLM_ENTITY_METAS
from .clm.events import event_registry as clm_event_registry
from .compliance_mod.entities import ENTITY_METAS as COMPLIANCE_ENTITY_METAS
from .compliance_mod.routes.risk_matrix import router as risk_matrix_router

ENTITY_METAS = [*COMPLIANCE_ENTITY_METAS, *CLM_ENTITY_METAS]


app = create_service_app(
    service_name="compliance",
    entity_metas=ENTITY_METAS,
    event_registry=clm_event_registry,
    extra_routers=[
        risk_matrix_router,
    ],
)
