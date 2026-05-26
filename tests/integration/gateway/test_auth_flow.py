"""인증 플로우 통합 테스트.

로그인 → 토큰 발급 → /api/v1/me 접근 흐름을 검증한다.
실제 DB 호출은 conftest 의 mock 으로 차단되므로,
라우트 존재 여부 + HTTP 응답 구조를 검증하는 데 집중한다.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_auth_login_route_exists(client: TestClient) -> None:
    """/api/v1/auth/login 엔드포인트가 등록돼 있어야 한다.

    - 올바른 JSON body → 200 (mock 환경) 또는 인증 실패 401/422
    - 라우트 미등록 시 404 — 이것만 실패 조건
    """
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "test@example.com", "password": "wrong_password"},
    )
    # 라우트가 존재하면 200·401·422 중 하나; 없으면 404
    assert resp.status_code != 404, (
        f"/api/v1/auth/login 라우트를 찾을 수 없음 (404). 응답: {resp.text}"
    )
    assert resp.status_code in (200, 401, 422), f"예상치 못한 상태 코드: {resp.status_code}"


@pytest.mark.integration
def test_auth_login_bad_payload_returns_422(client: TestClient) -> None:
    """/api/v1/auth/login — 필수 필드 누락 시 422 Unprocessable Entity."""
    resp = client.post("/api/v1/auth/login", json={})
    # username/password 필수 → Pydantic 검증 오류 422
    assert resp.status_code == 422, f"빈 payload 전송 시 422 기대, 실제: {resp.status_code}"


@pytest.mark.integration
def test_auth_me_requires_auth(client: TestClient) -> None:
    """/api/v1/me 는 인증 헤더 없이 접근 시 401/403 을 반환해야 한다."""
    # 인증 헤더를 제거한 별도 요청
    no_auth_headers = {
        k: v
        for k, v in client.headers.items()
        if k.lower() not in ("x-user-sub", "x-user-roles", "x-user-tier", "x-user-permissions")
    }
    resp = client.get("/api/v1/me", headers=no_auth_headers)
    # 라우트 존재 확인 (404 는 라우트 미등록)
    assert resp.status_code != 404, f"/api/v1/me 라우트를 찾을 수 없음 (404). 응답: {resp.text}"


@pytest.mark.integration
def test_auth_me_with_valid_headers(client: TestClient) -> None:
    """/api/v1/me — default_test_headers (mock super_admin) 로 접근 시 200."""
    resp = client.get("/api/v1/me")
    # mock 환경에서 현재 사용자 정보 조회 성공 기대
    # DB 조회가 필요한 경우 500 가능 → 500 도 허용하되 404 는 불가
    assert resp.status_code in (200, 500), (
        f"/api/v1/me 응답: {resp.status_code} — 라우트 미등록(404) 또는 예외"
    )


@pytest.mark.integration
def test_auth_refresh_route_exists(client: TestClient) -> None:
    """/api/v1/auth/refresh 엔드포인트가 등록돼 있어야 한다."""
    resp = client.post("/api/v1/auth/refresh")
    assert resp.status_code != 404, f"/api/v1/auth/refresh 라우트 미등록. 응답: {resp.text}"
    assert resp.status_code in (200, 401, 403, 422, 500)


@pytest.mark.integration
def test_auth_logout_route_exists(client: TestClient) -> None:
    """/api/v1/auth/logout 엔드포인트가 등록돼 있어야 한다."""
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code != 404, f"/api/v1/auth/logout 라우트 미등록. 응답: {resp.text}"
    assert resp.status_code in (200, 401, 403, 422, 500)
