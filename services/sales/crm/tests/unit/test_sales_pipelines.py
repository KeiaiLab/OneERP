"""영업파이프라인(SalesPipeline) API 엔드포인트 테스트 — Report.

M3 — Route → Service 분리 후 PipelineService.list_pipelines mock 으로 변경.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_crm_app.routes.sales_pipelines import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


@patch("oneerp_crm_app.routes.sales_pipelines.PipelineService")
def test_영업파이프라인_목록_조회(mock_svc_cls: MagicMock) -> None:
    """영업파이프라인 목록 API가 빈 결과를 정상 반환하는지 검증한다."""
    svc = MagicMock()
    svc.list_pipelines.return_value = {"data": [], "total": 0}
    mock_svc_cls.return_value = svc
    response = client.get("/api/v1/sales-pipelines/")
    assert response.status_code == 200


@patch("oneerp_crm_app.routes.sales_pipelines.PipelineService")
def test_영업파이프라인_목록_데이터(mock_svc_cls: MagicMock) -> None:
    """영업파이프라인 목록 API가 데이터를 정상 반환하는지 검증한다."""
    svc = MagicMock()
    svc.list_pipelines.return_value = {"data": [{"_id": "SPLN-001"}], "total": 1}
    mock_svc_cls.return_value = svc
    response = client.get("/api/v1/sales-pipelines/?page=1&page_size=10")
    assert response.json()["total"] == 1
