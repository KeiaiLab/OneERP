"""OneERP HR 서비스.

직원/인사발령/부서/직급/휴가유형/휴가신청/휴가잔액/근태를 제외한 엔티티는 EntityMeta 기반 자동 CRUD,
직원/인사발령/부서/직급/휴가유형/휴가신청/휴가잔액/근태는 보고라인/발령 워크벤치/조직도/직급체계/활성 카탈로그/승인 워크플로우/연차 자동화/체크인 로직 때문에 커스텀 라우트로 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .events.handlers import register_handlers
from .routes.attendances import router as attendances_router
from .routes.departments import router as departments_router
from .routes.designations import router as designations_router
from .routes.employee_transfers import router as employee_transfers_router
from .routes.employees import router as employees_router
from .routes.leave_applications import router as leave_applications_router
from .routes.leave_balances import router as leave_balances_router
from .routes.leave_types import router as leave_types_router

app = create_service_app(
    service_name="hr",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        employees_router,
        employee_transfers_router,
        attendances_router,
        departments_router,
        designations_router,
        leave_types_router,
        leave_applications_router,
        leave_balances_router,
    ],
)

# HR 도메인 이벤트 핸들러 등록 (Spec III Wave C-2 · accounting 패턴 미러)
register_handlers(event_registry)
