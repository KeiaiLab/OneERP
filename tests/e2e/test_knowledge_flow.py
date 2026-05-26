"""E2E: 지식베이스 플로우 — 작성 → 검색 → 포털 피드백 → 리뷰."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


class TestKnowledgeFlow:
    """지식베이스 사용자 시나리오를 검증한다."""

    def test_지식문서_게시후_검색과_포털피드백_리뷰가_동작한다(
        self,
        knowledge_client: httpx.Client,
    ) -> None:
        """작성자가 게시한 공개 문서가 검색/포털/리뷰 흐름에 연결된다."""
        create_resp = knowledge_client.post(
            "/api/v1/knowledge-articles",
            json={
                "title": "E2E 비밀번호 재설정",
                "content": "1. 로그인 화면에서 비밀번호 찾기를 누릅니다.\n2. 메일 링크로 새 비밀번호를 설정합니다.",
                "summary": "로그인 문제 해결",
                "category": "faq",
                "author": "지식관리자",
                "tags": ["faq", "보안"],
                "status": "published",
                "visibility": "public",
                "review_interval_days": 30,
            },
            headers=HEADERS,
        )
        assert create_resp.status_code == 201
        article_id = create_resp.json()["_id"]

        search_resp = knowledge_client.get(
            "/api/v1/knowledge-articles/search",
            params={"keyword": "비밀번호", "ai_suggest": "true"},
            headers=HEADERS,
        )
        assert search_resp.status_code == 200
        search_body = search_resp.json()
        assert search_body["total"] == 1
        assert search_body["ai_suggestions"][0]["article_id"] == article_id

        update_resp = knowledge_client.put(
            f"/api/v1/knowledge-articles/{article_id}",
            json={
                "content": "1. 로그인 화면에서 비밀번호 찾기를 누릅니다.\n2. 메일 링크를 열고 2단계 인증을 확인합니다.\n3. 새 비밀번호를 저장합니다.",
                "change_summary": "보안 단계 추가",
            },
            headers=HEADERS,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["current_version"] == 2

        diff_resp = knowledge_client.get(
            f"/api/v1/knowledge-articles/{article_id}/versions/diff",
            params={"from_version": 1, "to_version": 2},
            headers=HEADERS,
        )
        assert diff_resp.status_code == 200
        assert any(change["type"] in {"modify", "add"} for change in diff_resp.json()["changes"])

        portal_resp = knowledge_client.get(
            "/api/v1/portal/articles",
            params={"keyword": "비밀번호"},
            headers={"X-Tenant-Id": HEADERS["X-Tenant-Id"]},
        )
        assert portal_resp.status_code == 200
        assert portal_resp.json()["data"][0]["_id"] == article_id

        feedback_resp = knowledge_client.post(
            f"/api/v1/portal/articles/{article_id}/feedback",
            json={"is_helpful": True, "comment": "셀프로 해결했습니다."},
            headers={"X-Tenant-Id": HEADERS["X-Tenant-Id"]},
        )
        assert feedback_resp.status_code == 200
        assert feedback_resp.json()["helpful_count"] == 1

        reminder_resp = knowledge_client.post(
            "/api/v1/knowledge-articles/review-reminders/run",
            headers=HEADERS,
        )
        assert reminder_resp.status_code == 200
        assert reminder_resp.json()["total"] == 0

        review_resp = knowledge_client.post(
            f"/api/v1/knowledge-articles/{article_id}/review",
            headers=HEADERS,
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["article_id"] == article_id
