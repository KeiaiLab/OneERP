"""서비스 레지스트리 API 라우터."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

from oneerp_crm_app.models.service_registry import ServiceInfo

router = APIRouter(prefix="/api/v1/services", tags=["서비스 레지스트리"])


def _build_registry() -> list[ServiceInfo]:
    """환경변수 기반으로 서비스 목록을 구성한다."""
    selling_url = os.environ.get("ONEERP_SELLING_URL", "http://selling:8000")
    stock_url = os.environ.get("ONEERP_STOCK_URL", "http://stock:8000")
    accounting_url = os.environ.get("ONEERP_ACCOUNTING_URL", "http://accounting:8000")
    services = [
        ServiceInfo(
            name="selling",
            url=selling_url,
            health_url=f"{selling_url}/health",
            status="registered",
        ),
        ServiceInfo(
            name="stock",
            url=stock_url,
            health_url=f"{stock_url}/health",
            status="registered",
        ),
        ServiceInfo(
            name="accounting",
            url=accounting_url,
            health_url=f"{accounting_url}/health",
            status="registered",
        ),
    ]
    return services  # noqa: RET504


@router.get("")
def list_services() -> dict[str, Any]:
    """등록된 서비스 목록을 반환한다."""
    services = _build_registry()
    return {
        "data": [s.model_dump() for s in services],
        "total": len(services),
    }
