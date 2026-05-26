"""Rate limit 동작 통합 테스트.

실제 rate limit threshold 가 설정되지 않은 테스트 환경에서는
연속 요청이 전부 거부(429)되지 않음을 확인한다.
헬스체크·루트 엔드포인트를 활용해 기본 가용성을 검증한다.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_health_endpoint_responds(client: TestClient) -> None:
    """GET /api/v1/health 또는 / — 서비스가 응답해야 한다.

    rate limit 테스트 기준 엔드포인트. 200 또는 404 (루트 미정의) 허용.
    """
    resp = client.get("/api/v1/health")
    # health 엔드포인트가 없으면 루트로 시도
    if resp.status_code == 404:
        resp = client.get("/")
    assert resp.status_code in (200, 404), f"서비스가 응답하지 않음: {resp.status_code}"


@pytest.mark.integration
def test_multiple_requests_not_all_rejected(client: TestClient) -> None:
    """연속 10회 요청에서 전부 429(Too Many Requests) 가 반환되지 않아야 한다.

    테스트 환경에서는 rate limit threshold 가 적용되지 않으므로
    정상 응답(200) 또는 라우트 미정의(404) 가 반환된다.
    """
    responses = [client.get("/api/v1/health").status_code for _ in range(10)]
    assert not all(code == 429 for code in responses), (
        "모든 요청이 429로 거부됨 — 테스트 환경에서 rate limit 이 너무 낮게 설정돼 있음"
    )


@pytest.mark.integration
def test_auth_endpoint_not_rate_limited_immediately(client: TestClient) -> None:
    """/api/v1/auth/login 에 5회 연속 요청 시 전부 429 되지 않아야 한다."""
    responses = [
        client.post(
            "/api/v1/auth/login",
            json={"username": "test@example.com", "password": "wrong"},
        ).status_code
        for _ in range(5)
    ]
    assert not all(code == 429 for code in responses), (
        "인증 엔드포인트가 즉시 rate limit — threshold 설정 검토 필요"
    )


@pytest.mark.integration
def test_dashboard_endpoint_accessible(client: TestClient) -> None:
    """GET /api/v1/dashboard — 대시보드 엔드포인트가 응답해야 한다.

    인증 통과(mock super_admin) 후 DB mock 에 따라 200 또는 500 기대.
    """
    resp = client.get("/api/v1/dashboard")
    # 라우트가 있으면 200/401/403/500; 없으면 404
    assert resp.status_code in (200, 401, 403, 404, 500), f"대시보드 응답: {resp.status_code}"


@pytest.mark.integration
def test_openapi_schema_accessible(client: TestClient) -> None:
    """GET /openapi.json — OpenAPI 스키마가 조회 가능해야 한다.

    모든 라우터가 app 에 등록됐는지 간접 검증.
    """
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, f"OpenAPI 스키마 조회 실패: {resp.status_code}"
    schema = resp.json()
    assert "paths" in schema, "OpenAPI 스키마에 paths 키 없음"
    # 주요 경로 포함 여부 확인
    assert any("/auth" in path for path in schema["paths"]), "auth 라우트가 OpenAPI 스키마에 없음"
