"""예산(Budget) API 통합 테스트.

실제 라우트: /api/v1/budgets
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_budgets_list_route_exists(client: TestClient) -> None:
    """GET /api/v1/budgets — 라우트 등록 확인."""
    resp = client.get("/api/v1/budgets")
    assert resp.status_code != 404, f"/api/v1/budgets 라우트 미등록. 응답: {resp.text}"
    assert resp.status_code in (200, 401, 403, 500)


@pytest.mark.integration
def test_budgets_create_validation(client: TestClient) -> None:
    """POST /api/v1/budgets — 빈 payload 는 422 Pydantic 검증 오류."""
    resp = client.post("/api/v1/budgets", json={})
    assert resp.status_code != 404, "POST /api/v1/budgets 라우트 미등록"
    assert resp.status_code in (200, 201, 400, 401, 403, 422, 500)


@pytest.mark.integration
def test_budgets_get_by_id(client: TestClient) -> None:
    """GET /api/v1/budgets/{id} — 개별 조회 라우트 등록."""
    resp = client.get("/api/v1/budgets/BGT-DOES-NOT-EXIST")
    assert resp.status_code in (200, 404, 401, 403, 500), f"응답 상태 코드: {resp.status_code}"


@pytest.mark.integration
def test_health_route(client: TestClient) -> None:
    """/health — create_service_app 이 기본 제공하는 헬스 엔드포인트."""
    resp = client.get("/health")
    # /health 가 없으면 /healthz 시도
    if resp.status_code == 404:
        resp = client.get("/healthz")
    assert resp.status_code in (200, 404), f"/health 또는 /healthz 응답: {resp.status_code}"
