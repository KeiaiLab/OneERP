"""지식 문서 공개 포털 액션 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class Test포털지식검색라우트:
    """지식 포털 검색 라우트 테스트."""

    def test_공개_문서_검색_라우트(self, test_client) -> None:
        """포털 검색 라우트가 공개 문서 목록을 반환한다."""
        with patch(
            "oneerp_knowledge_app.routes.article_actions.ArticleService"
        ) as mock_service_cls:
            svc = MagicMock()
            svc.list_portal_articles.return_value = [
                {"_id": "KA-001", "title": "비밀번호 재설정", "visibility": "public"},
            ]
            mock_service_cls.return_value = svc

            resp = test_client.get("/api/v1/portal/articles?keyword=비밀번호")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["_id"] == "KA-001"
        svc.list_portal_articles.assert_called_once_with(
            keyword="비밀번호",
            category=None,
            tag=None,
        )


class Test지식문서라우트:
    """지식 문서 커스텀 라우트 테스트."""

    def test_AI_추천_검색_라우트(self, test_client) -> None:
        """검색 라우트는 ai_suggest=true일 때 추천 결과를 함께 반환한다."""
        with patch(
            "oneerp_knowledge_app.routes.article_actions.ArticleService"
        ) as mock_service_cls:
            svc = MagicMock()
            svc.search_articles.return_value = [
                {"_id": "KA-001", "title": "비밀번호 재설정"},
            ]
            svc.suggest_articles.return_value = [
                {"article_id": "KA-001", "title": "비밀번호 재설정", "score": 0.91},
            ]
            mock_service_cls.return_value = svc

            resp = test_client.get(
                "/api/v1/knowledge-articles/search?keyword=비밀번호&ai_suggest=true"
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["ai_suggestions"][0]["article_id"] == "KA-001"
        svc.suggest_articles.assert_called_once_with("비밀번호", visibility=None)

    def test_버전_diff_라우트(self, test_client) -> None:
        """버전 비교 라우트가 변경 내역을 반환한다."""
        with patch(
            "oneerp_knowledge_app.routes.article_actions.ArticleService"
        ) as mock_service_cls:
            svc = MagicMock()
            svc.get_version_diff.return_value = {
                "article_id": "KA-001",
                "from_version": 1,
                "to_version": 2,
                "changes": [{"type": "modify", "line": 2, "old_text": "이전", "new_text": "현재"}],
            }
            mock_service_cls.return_value = svc

            resp = test_client.get(
                "/api/v1/knowledge-articles/KA-001/versions/diff?from_version=1&to_version=2"
            )

        assert resp.status_code == 200
        assert resp.json()["changes"][0]["type"] == "modify"
        svc.get_version_diff.assert_called_once_with("KA-001", from_version=1, to_version=2)

    def test_리뷰_주기_실행_라우트(self, test_client) -> None:
        """리뷰 주기 실행 라우트가 리뷰 대상 문서를 반환한다."""
        with patch(
            "oneerp_knowledge_app.routes.article_actions.ArticleService"
        ) as mock_service_cls:
            svc = MagicMock()
            svc.run_review_due_check.return_value = [
                {"article_id": "KA-001", "days_since_review": 45},
            ]
            mock_service_cls.return_value = svc

            resp = test_client.post("/api/v1/knowledge-articles/review-reminders/run")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["article_id"] == "KA-001"
        svc.run_review_due_check.assert_called_once()


class Test포털피드백라우트:
    """지식 포털 피드백 라우트 테스트."""

    def test_공개_문서_피드백_라우트(self, test_client) -> None:
        """포털 피드백 라우트가 도움됨 집계를 반환한다."""
        with patch(
            "oneerp_knowledge_app.routes.article_actions.ArticleService"
        ) as mock_service_cls:
            svc = MagicMock()
            svc.submit_feedback.return_value = {
                "article_id": "KA-001",
                "helpful_count": 4,
                "not_helpful_count": 1,
            }
            mock_service_cls.return_value = svc

            resp = test_client.post(
                "/api/v1/portal/articles/KA-001/feedback",
                json={"is_helpful": True, "comment": "바로 해결됐습니다"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["helpful_count"] == 4
        assert body["not_helpful_count"] == 1
        svc.submit_feedback.assert_called_once_with(
            article_id="KA-001",
            is_helpful=True,
            comment="바로 해결됐습니다",
            user_id="test-user",
        )
