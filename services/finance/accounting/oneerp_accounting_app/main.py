"""OneERP 회계(Accounting) 서비스.

11개 엔티티는 EntityMeta 기반 자동 CRUD,
8개 엔티티는 커스텀 라우트로 직접 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.accounting_periods import router as accounting_periods_router
from .routes.accounts import router as accounts_router
from .routes.accounts_payable import router as accounts_payable_router
from .routes.accounts_receivable import router as accounts_receivable_router
from .routes.budgets import router as budgets_router
from .routes.cost_centers import router as cost_centers_router
from .routes.etax_invoices import router as etax_invoices_router
from .routes.general_ledger_entries import router as general_ledger_entries_router
from .routes.journal_entries import router as journal_entries_router
from .routes.reports import router as reports_router
from .routes.vat_returns import router as vat_returns_router

app = create_service_app(
    service_name="accounting",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        accounting_periods_router,
        accounts_router,
        journal_entries_router,
        budgets_router,
        cost_centers_router,
        general_ledger_entries_router,
        accounts_receivable_router,
        accounts_payable_router,
        etax_invoices_router,
        reports_router,
        vat_returns_router,
    ],
)
