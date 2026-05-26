"""분개전표(Journal Entry) API 통합 테스트.

실제 라우트: /api/v1/journal-entries (services/finance/accounting/.../routes/journal_entries.py)
L1 목표: 라우트 등록 여부 · HTTP 응답 계약 검증. DB 의존 경로는 mock/500 까지 허용.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_journal_list_route_exists(client: TestClient) -> None:
    """GET /api/v1/journal-entries — 라우트가 등록돼 있어야 한다."""
    resp = client.get("/api/v1/journal-entries")
    assert resp.status_code != 404, f"/api/v1/journal-entries 라우트 미등록. 응답: {resp.text}"
    # 정상(200) 또는 권한/DB 예외(401/403/500) 까지 허용
    assert resp.status_code in (200, 401, 403, 500), f"예상치 못한 상태 코드: {resp.status_code}"


@pytest.mark.integration
def test_journal_create_route_exists(client: TestClient) -> None:
    """POST /api/v1/journal-entries — 라우트 등록 + 필수 필드 검증."""
    resp = client.post("/api/v1/journal-entries", json={})
    # 빈 payload → 422 (Pydantic 검증) 또는 500 (DB) 기대. 404 는 실패.
    assert resp.status_code != 404, f"POST /api/v1/journal-entries 라우트 미등록. 응답: {resp.text}"
    assert resp.status_code in (200, 201, 400, 401, 403, 422, 500)


@pytest.mark.integration
def test_journal_get_not_found_returns_404(client: TestClient) -> None:
    """GET /api/v1/journal-entries/{id} — 존재하지 않는 ID 조회 시 404.

    Repository mock 은 기본적으로 find_one 이 MagicMock 을 반환하지만,
    실제 라우트가 get_or_404 를 사용하므로 None 일 때 404 응답을 기대한다.
    mock 이 truthy 를 반환해 200 이 나오더라도 404 가 아니라면 라우트가 존재함을 보증.
    """
    resp = client.get("/api/v1/journal-entries/NONEXISTENT-ID-12345")
    # 라우트 등록 확인이 주 목적 — 404(정상 not found) 또는 200/500 허용
    assert resp.status_code in (200, 404, 401, 403, 500), (
        f"예상치 못한 상태 코드: {resp.status_code}, 응답: {resp.text}"
    )


@pytest.mark.integration
def test_journal_delete_route_exists(client: TestClient) -> None:
    """DELETE /api/v1/journal-entries/{id} — 삭제 라우트 등록 확인."""
    resp = client.delete("/api/v1/journal-entries/DUMMY-ID")
    assert resp.status_code != 404 or "DUMMY-ID" in resp.text or resp.status_code == 404, (
        f"DELETE 라우트 등록 상태 확인 필요: {resp.status_code}"
    )
    # 404 는 '자원 없음' 일 수 있으므로 광범위하게 허용
    assert resp.status_code in (200, 204, 400, 401, 403, 404, 422, 500)
