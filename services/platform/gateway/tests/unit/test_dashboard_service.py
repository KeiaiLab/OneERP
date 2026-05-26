"""대시보드 KPI 집계 서비스 + SSE 스트리밍 단위 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_gateway_app.routes.dashboard import admin_router, router
from oneerp_gateway_app.services.dashboard_service import DashboardService

_app = FastAPI()
_app.include_router(router)
_app.include_router(admin_router)
client = TestClient(_app)

# 인증 헤더 상수
REGULAR_USER_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "user-001",
    "X-User-Roles": "user",
    "X-User-Tier": "regular",
    "X-User-Permissions": "dashboard:read",
}

SUPER_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "admin-user",
    "X-User-Roles": "admin",
    "X-User-Tier": "super_admin",
    "X-User-Permissions": "*:*",
}

TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


# ── KPI 구조 검증 ──


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_KPI_구조_모든_섹션_존재(mock_repo_cls: MagicMock) -> None:
    """get_kpis가 sales/buying/stock/approval/hr 섹션을 모두 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    mock_repo_cls.return_value = repo

    service = DashboardService("test-tenant")
    kpis = service.get_kpis()

    assert "sales" in kpis
    assert "buying" in kpis
    assert "stock" in kpis
    assert "approval" in kpis
    assert "hr" in kpis
    assert "generated_at" in kpis


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_KPI_빈_데이터_기본값_0(mock_repo_cls: MagicMock) -> None:
    """데이터가 없을 때 모든 KPI가 0을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    mock_repo_cls.return_value = repo

    service = DashboardService("test-tenant")
    kpis = service.get_kpis()

    assert kpis["sales"]["monthly_sales"] == 0
    assert kpis["sales"]["growth_rate"] == 0.0
    assert kpis["sales"]["outstanding_receivables"] == 0
    assert kpis["buying"]["pending_purchase_orders"] == 0
    assert kpis["buying"]["monthly_purchases"] == 0
    assert kpis["stock"]["low_stock_items"] == 0
    assert kpis["stock"]["stock_turnover_rate"] == 0.0
    assert kpis["approval"]["pending_approvals"] == 0
    assert kpis["hr"]["total_employees"] == 0
    assert kpis["hr"]["this_month_payroll"] == 0


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_KPI_매출_데이터_집계(mock_repo_cls: MagicMock) -> None:
    """매출 주문 데이터가 있을 때 monthly_sales를 올바르게 합산한다."""
    repo = MagicMock()
    # 이번 달 주문: 첫 번째 find_many 호출
    # 전월 주문: 두 번째 find_many 호출
    # AR: 세 번째 find_many 호출
    repo.find_many.side_effect = [
        # 이번 달 매출
        [{"grand_total": 100000}, {"grand_total": 200000}],
        # 전월 매출
        [{"grand_total": 150000}],
        # 미수금
        [{"outstanding_amount": 50000}],
        # 구매 PO (monthly)
        [],
        # 결재 KPI
        [],
        # 급여
        [],
    ]
    repo.count.return_value = 0
    mock_repo_cls.return_value = repo

    service = DashboardService("test-tenant")
    kpis = service.get_kpis()

    assert kpis["sales"]["monthly_sales"] == 300000
    assert kpis["sales"]["outstanding_receivables"] == 50000
    # 성장률: (300000 - 150000) / 150000 * 100 = 100.0%
    assert kpis["sales"]["growth_rate"] == 100.0


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_KPI_사용자별_결재_집계(mock_repo_cls: MagicMock) -> None:
    """get_kpis_for_user가 사용자별 대기 결재를 포함한다."""
    repo = MagicMock()
    active_requests = [
        {
            "_id": "AR-001",
            "status": "submitted",
            "current_step": 1,
            "approval_lines": [
                {"step": 1, "approver": "user-001", "status": "pending"},
            ],
        },
        {
            "_id": "AR-002",
            "status": "pending",
            "current_step": 2,
            "approval_lines": [
                {"step": 1, "approver": "manager-001", "status": "approved"},
                {"step": 2, "approver": "user-001", "status": "pending"},
                {"step": 2, "approver": "legal-001", "status": "pending"},
            ],
        },
        {
            "_id": "AR-003",
            "status": "submitted",
            "current_step": 1,
            "approval_lines": [
                {"step": 1, "approver": "finance-001", "status": "pending"},
            ],
        },
    ]
    repo.find_many.side_effect = [
        [],  # 이번 달 매출
        [],  # 전월 매출
        [],  # 미수금
        [],  # 이번 달 구매
        active_requests,  # 전체 대기 결재
        [],  # 이번 달 급여
        active_requests,  # 사용자 기준 대기 결재
    ]
    repo.count.side_effect = [
        # _aggregate_buying → pending PO count
        3,
        # _aggregate_stock → low_stock_items
        2,
        # _aggregate_stock → item_count
        10,
        # _aggregate_stock → outgoing_count
        5,
        # _aggregate_hr → total_employees
        50,
    ]
    mock_repo_cls.return_value = repo

    service = DashboardService("test-tenant")
    kpis = service.get_kpis_for_user("user-001")

    assert kpis["approval"]["pending_approvals"] == 3
    assert kpis["approval"]["my_pending_approvals"] == 2


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_월별_매출_차트_데이터_집계(mock_repo_cls: MagicMock) -> None:
    """월별 매출 차트가 최근 월별 합계를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {"created_at": "2026-04-02T00:00:00+00:00", "grand_total": 100000, "docstatus": 1},
        {"created_at": "2026-04-18T00:00:00+00:00", "grand_total": 50000, "docstatus": 1},
        {"created_at": "2026-03-05T00:00:00+00:00", "grand_total": 70000, "docstatus": 1},
    ]
    mock_repo_cls.return_value = repo

    service = DashboardService("test-tenant")
    chart = service.get_monthly_sales_chart(months=2)

    assert chart == [
        {"month": "2026-03", "amount": 70000},
        {"month": "2026-04", "amount": 150000},
    ]


# ── API 엔드포인트 테스트 ──


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_KPI_API_정상_응답(mock_repo_cls: MagicMock) -> None:
    """GET /api/v1/dashboard/kpis가 200을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    mock_repo_cls.return_value = repo

    response = client.get("/api/v1/dashboard/kpis", headers=REGULAR_USER_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "sales" in data
    assert "buying" in data


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_매출_차트_API_정상_응답(mock_repo_cls: MagicMock) -> None:
    """GET /api/v1/dashboard/sales-chart가 월별 매출 배열을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {"created_at": "2026-04-02T00:00:00+00:00", "grand_total": 100000, "docstatus": 1},
    ]
    mock_repo_cls.return_value = repo

    response = client.get("/api/v1/dashboard/sales-chart", headers=REGULAR_USER_HEADERS)
    assert response.status_code == 200
    assert response.json() == [{"month": "2026-04", "amount": 100000}]


# ── SSE 스트리밍 테스트 ──


@patch("oneerp_gateway_app.routes.dashboard.asyncio")
@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_SSE_스트리밍_응답_타입(mock_repo_cls: MagicMock, mock_asyncio: MagicMock) -> None:
    """GET /api/v1/dashboard/kpis/stream이 text/event-stream을 반환한다."""
    import asyncio as real_asyncio

    # AsyncMock으로 sleep을 대체하여 CancelledError를 발생시킨다
    mock_asyncio.sleep = AsyncMock(side_effect=real_asyncio.CancelledError)
    mock_asyncio.CancelledError = real_asyncio.CancelledError

    repo = MagicMock()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    mock_repo_cls.return_value = repo

    with client.stream(
        "GET", "/api/v1/dashboard/kpis/stream", headers=REGULAR_USER_HEADERS
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        # 첫 번째 이벤트를 읽는다
        for line in response.iter_lines():
            if line.startswith("data:"):
                import json

                payload = json.loads(line[5:].strip())
                assert "sales" in payload
                break


@patch("oneerp_gateway_app.routes.dashboard.asyncio")
@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_SSE_스트리밍_캐시_헤더(mock_repo_cls: MagicMock, mock_asyncio: MagicMock) -> None:
    """SSE 응답에 Cache-Control: no-cache 헤더가 포함된다."""
    import asyncio as real_asyncio

    mock_asyncio.sleep = AsyncMock(side_effect=real_asyncio.CancelledError)
    mock_asyncio.CancelledError = real_asyncio.CancelledError

    repo = MagicMock()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    mock_repo_cls.return_value = repo

    with client.stream(
        "GET", "/api/v1/dashboard/kpis/stream", headers=REGULAR_USER_HEADERS
    ) as response:
        assert response.headers.get("cache-control") == "no-cache"


# ── 테넌트 개요 (super_admin) ──


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_테넌트_개요_super_admin_성공(mock_repo_cls: MagicMock) -> None:
    """super_admin이 테넌트 개요를 조회하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {"_id": "TNT-001", "tenant_name": "A사", "plan": "standard", "is_active": True},
    ]
    repo.count.return_value = 5
    mock_repo_cls.return_value = repo

    response = client.get("/api/v1/admin/dashboard/tenants", headers=SUPER_ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "tenants" in data
    assert len(data["tenants"]) == 1
    assert data["tenants"][0]["tenant_name"] == "A사"


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_테넌트_개요_일반사용자_403(mock_repo_cls: MagicMock) -> None:
    """일반 사용자가 테넌트 개요에 접근하면 403을 반환한다."""
    mock_repo_cls.return_value = MagicMock()

    response = client.get("/api/v1/admin/dashboard/tenants", headers=REGULAR_USER_HEADERS)
    assert response.status_code == 403


@patch("oneerp_gateway_app.services.dashboard_service.Repository")
def test_테넌트_개요_tenant_admin_403(mock_repo_cls: MagicMock) -> None:
    """tenant_admin이 super_admin 전용 라우트에 접근하면 403을 반환한다."""
    mock_repo_cls.return_value = MagicMock()

    response = client.get("/api/v1/admin/dashboard/tenants", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 403
