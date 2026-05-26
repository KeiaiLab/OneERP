"""OneERP Payroll 서비스.

엔티티 메타 기반 CRUD 라우터 + 커스텀 라우트 혼합 구성.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.payroll_entries import router as payroll_entries_router
from .routes.payroll_tax_returns import router as payroll_tax_returns_router
from .routes.payslip_reports import router as payslip_reports_router
from .routes.retirement_pays import router as retirement_pays_router
from .routes.salary_components import router as salary_components_router
from .routes.salary_slips import router as salary_slips_router
from .routes.salary_structures import router as salary_structures_router
from .routes.social_insurances import router as social_insurances_router
from .routes.withholding_taxes import router as withholding_taxes_router
from .routes.year_end_settlements import router as year_end_settlements_router

app = create_service_app(
    service_name="payroll",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        salary_structures_router,
        salary_slips_router,
        salary_components_router,
        payroll_entries_router,
        social_insurances_router,
        withholding_taxes_router,
        year_end_settlements_router,
        retirement_pays_router,
        payroll_tax_returns_router,
        payslip_reports_router,
    ],
)
