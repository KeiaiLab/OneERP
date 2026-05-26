"""OneERP API Gateway 서비스.

HR/Payroll/Expenses/CRM/Assets/Projects/Quality 도메인은 독립 서비스로 분리됨.
Gateway는 인증/전자결재/Setup을 관리한다.
모든 엔티티는 커스텀 라우트로 직접 관리한다
(인증/관리자/전자결재 등 비표준 로직 포함).
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.admin import router as admin_router
from .routes.approval_actions import router as approval_actions_router
from .routes.approval_lines import router as approval_lines_router
from .routes.approval_requests import router as approval_requests_router
from .routes.approval_templates import router as approval_templates_router
from .routes.auth import router as auth_router
from .routes.business_registrations import router as business_registrations_router
from .routes.companies import router as companies_router
from .routes.currencies import router as currencies_router
from .routes.dashboard import router as dashboard_router
from .routes.delegation_rules import router as delegation_rules_router
from .routes.me import router as me_router
from .routes.naming_series import router as naming_series_router
from .routes.notification_rules import router as notification_rules_router
from .routes.notification_templates import router as notification_templates_router
from .routes.retention_policies import router as retention_policies_router
from .routes.role_permissions import router as role_permissions_router
from .routes.roles import router as roles_router
from .routes.system_settings import router as system_settings_router
from .routes.tenants import router as tenants_router
from .routes.users import router as users_router
from .routes.workflow_definitions import router as workflow_definitions_router
from .routes.workflow_engine import router as workflow_engine_router
from .routes.workflow_rules import router as workflow_rules_router

app = create_service_app(
    service_name="gateway",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        # 인증
        auth_router,
        me_router,
        # 관리자
        admin_router,
        # 전자결재
        approval_templates_router,
        approval_requests_router,
        approval_lines_router,
        approval_actions_router,
        delegation_rules_router,
        # Setup
        business_registrations_router,
        companies_router,
        workflow_rules_router,
        notification_templates_router,
        retention_policies_router,
        currencies_router,
        users_router,
        roles_router,
        role_permissions_router,
        workflow_definitions_router,
        workflow_engine_router,
        notification_rules_router,
        naming_series_router,
        system_settings_router,
        tenants_router,
        # 대시보드
        dashboard_router,
    ],
)
