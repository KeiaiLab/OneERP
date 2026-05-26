"""게이트 함수 묶음 · 공용 경로 매핑 헬퍼."""

from __future__ import annotations

from pathlib import Path

# 모듈 → 서비스 클러스터 경로 (실제 services/ 구조 기반)
_MODULE_CLUSTER: dict[str, str] = {
    "gateway": "platform/gateway",
    "accounting": "finance/accounting",
    "hr": "hr/hr",
    "directory": "platform/gateway",
    "selling": "sales/selling",
    "buying": "scm/buying",
    "stock": "scm/stock",
    "payroll": "finance/payroll",
    "portal": "portal/portal_core",
    "projects": "collab/projects",
    "expenses": "finance/expenses",
    "crm": "sales/crm",
    "advanced-planning": "logistics/advanced-planning",
    "analytics": "platform/analytics",
    "assets": "assets/assets",
    "board": "collab/board",
    "calendar": "collab/calendar",
    "clm": "compliance/compliance",
    "compliance": "compliance/compliance",
    "consolidation": "finance/accounting",
    "documents": "collab/documents",
    "ecommerce": "sales/commerce",
    "ehs": "ehs/ehs",
    "esg": "compliance/compliance",
    "fleet": "logistics/logistics",
    "gtm": "marketing/gtm",
    "integration-hub": "platform/integration-hub",
    "iot": "platform/iot",
    "knowledge": "collab/knowledge",
    "lms": "hr/learning",
    "mail": "portal/portal_comms",
    "maintenance": "scm/manufacturing",
    "manufacturing": "scm/manufacturing",
    "marketing": "marketing/marketing",
    "marketing-automation": "marketing/marketing-automation",
    "messenger": "portal/portal_comms",
    "plm": "assets/plm",
    "pos": "sales/pos",
    "quality": "scm/qm",
    "rental": "sales/selling",
    "reservation": "sales/reservation",
    "rpa": "platform/rpa",
    "subscriptions": "sales/selling",
    "survey": "collab/survey",
    "tms": "logistics/logistics",
    "wiki": "collab/wiki",
    "workreport": "hr/hr",
}


def module_service_dir(module: str) -> Path:
    """모듈명 → 서비스 클러스터 디렉토리 경로."""
    cluster = _MODULE_CLUSTER.get(module, module)
    return Path(f"services/{cluster}")


def module_runbook_path(module: str) -> Path:
    """모듈명 → 런북 문서 경로."""
    return Path(f"docs/ops/runbook-{module}.md")
