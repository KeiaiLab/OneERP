"""E2E: 고객지원 플로우 — Issue 생성 → 해결 → 종료."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestSupportFlow:
    """고객지원 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_이슈_생성_해결_종료(self, crm_client: httpx.Client) -> None:
        """Issue 생성 → resolve → close 전체 라이프사이클."""
        # 이슈 생성
        resp = crm_client.post(
            "/api/v1/issues",
            json={
                "subject": "E2E 로그인 오류",
                "description": "로그인 시 500 에러가 발생합니다",
                "priority": "high",
                "assigned_to": "dev-user",
            },
        )
        assert resp.status_code == 201
        issue_id = resp.json()["id"]

        # 조회
        resp = crm_client.get(f"/api/v1/issues/{issue_id}")
        assert resp.status_code == 200
        issue = resp.json()
        assert issue["subject"] == "E2E 로그인 오류"
        assert issue["priority"] == "high"

        # 수정
        resp = crm_client.put(
            f"/api/v1/issues/{issue_id}",
            json={
                "priority": "critical",
            },
        )
        assert resp.status_code == 200

        # 해결
        resp = crm_client.post(
            f"/api/v1/issues/{issue_id}/resolve",
            json={
                "resolution": "세션 타임아웃 설정을 수정하여 해결",
            },
        )
        assert resp.status_code == 200

        # 종료
        resp = crm_client.post(f"/api/v1/issues/{issue_id}/close")
        assert resp.status_code == 200

    def test_이슈_목록_조회(self, crm_client: httpx.Client) -> None:
        """이슈 목록 페이지네이션 검증."""
        # 이슈 여러 개 생성
        for i in range(3):
            crm_client.post(
                "/api/v1/issues",
                json={
                    "subject": f"E2E 테스트 이슈 {i}",
                    "priority": "medium",
                },
            )

        resp = crm_client.get("/api/v1/issues", params={"page": 1, "page_size": 10})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 3
        assert len(body["data"]) >= 3

    def test_이슈_삭제(self, crm_client: httpx.Client) -> None:
        """이슈 생성 → 삭제."""
        resp = crm_client.post(
            "/api/v1/issues",
            json={
                "subject": "삭제 테스트 이슈",
                "priority": "low",
            },
        )
        issue_id = resp.json()["id"]

        resp = crm_client.delete(f"/api/v1/issues/{issue_id}")
        assert resp.status_code == 204
