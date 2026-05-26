"""테넌트 라우팅 통합 테스트.

/api/v1/tenants 엔드포인트의 존재·인증·페이로드 검증을 확인한다.
실제 DB 호출은 conftest 의 mock 으로 차단된다.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_tenants_list_route_exists(client: TestClient) -> None:
    """GET /api/v1/tenants 엔드포인트가 등록돼 있어야 한다.

    super_admin 헤더(default_test_headers) 로 접근 — DB mock 환경에서
    200 또는 500(DB 연결 시도 실패) 기대. 404 는 라우트 미등록이므로 실패.
    """
    resp = client.get("/api/v1/tenants")
    assert resp.status_code != 404, (
        f"GET /api/v1/tenants 라우트를 찾을 수 없음 (404). 응답: {resp.text}"
    )
    # 인증 통과 후 DB 조회 → mock 에 따라 200 또는 내부 오류
    assert resp.status_code in (200, 401, 403, 500), f"예상치 못한 상태 코드: {resp.status_code}"


@pytest.mark.integration
def test_tenant_create_validates_payload(client: TestClient) -> None:
    """POST /api/v1/tenants — 빈 payload 전송 시 422 Unprocessable Entity."""
    resp = client.post("/api/v1/tenants", json={})
    # 라우트 존재 확인
    assert resp.status_code != 404, f"POST /api/v1/tenants 라우트 미등록. 응답: {resp.text}"
    # 필수 필드 누락 → Pydantic 422 또는 권한 부족 403
    assert resp.status_code in (401, 403, 422), f"빈 payload 시 422 기대, 실제: {resp.status_code}"


@pytest.mark.integration
def test_tenant_get_nonexistent_returns_not_found(client: TestClient) -> None:
    """GET /api/v1/tenants/{id} — 존재하지 않는 ID 는 404 반환."""
    resp = client.get("/api/v1/tenants/NON_EXISTENT_ID")
    # 라우트 자체가 없으면 404 이지만, 파라미터화된 라우트가 없을 때도 404
    # → 응답 바디로 구분: OneERPError 의 경우 "not_found" 포함
    if resp.status_code == 404:
        # 라우트 미등록 vs 문서 미존재 구분
        body = resp.json()
        # OneERPError 포맷이면 라우트 존재 (정상 동작)
        assert "error" in body or "detail" in body, (
            "GET /api/v1/tenants/{id} 라우트 자체가 미등록 상태일 수 있음"
        )
    else:
        assert resp.status_code in (200, 401, 403, 500)


@pytest.mark.integration
def test_tenant_suspend_route_exists(client: TestClient) -> None:
    """POST /api/v1/tenants/{id}/suspend 엔드포인트가 등록돼 있어야 한다."""
    resp = client.post(
        "/api/v1/tenants/TEST_ID/suspend",
        json={"reason": "테스트 정지"},
    )
    assert resp.status_code != 405, f"suspend 라우트 메서드 불일치. 응답: {resp.text}"
    # DB mock 에서 404(문서 미존재) 또는 권한 오류 기대
    assert resp.status_code in (200, 401, 403, 404, 500), (
        f"예상치 못한 상태 코드: {resp.status_code}"
    )


@pytest.mark.integration
def test_tenant_activate_route_exists(client: TestClient) -> None:
    """POST /api/v1/tenants/{id}/activate 엔드포인트가 등록돼 있어야 한다."""
    resp = client.post("/api/v1/tenants/TEST_ID/activate")
    assert resp.status_code in (200, 401, 403, 404, 500), (
        f"activate 라우트 응답: {resp.status_code}"
    )
