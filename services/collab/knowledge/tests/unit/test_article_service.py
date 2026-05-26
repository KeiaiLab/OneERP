"""지식 문서 서비스(ArticleService) 단위 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """ArticleService와 mock 레포지토리를 생성한다."""
    with patch("oneerp_knowledge_app.services.article_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_knowledge_app.services.article_service import ArticleService

        service = ArticleService(tenant_id="test-tenant")
    return (
        service,
        repos["knowledge_articles"],
        repos.get("knowledge_article_feedback", MagicMock()),
        repos.get("knowledge_article_versions", MagicMock()),
        repos.get("knowledge_article_review_notifications", MagicMock()),
    )


class Test문서검색:
    """지식 문서 검색 테스트."""

    def test_제목_검색(self) -> None:
        """제목에 키워드가 포함된 문서를 반환한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_many.return_value = [
            {"title": "Python 가이드", "tags": [], "content": "", "status": "published"},
            {"title": "Java 가이드", "tags": [], "content": "", "status": "published"},
        ]

        results = service.search_articles("Python")

        assert len(results) == 1
        assert results[0]["title"] == "Python 가이드"

    def test_태그_검색(self) -> None:
        """태그에 키워드가 포함된 문서를 반환한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_many.return_value = [
            {
                "title": "API 문서",
                "tags": ["python", "fastapi"],
                "content": "",
                "status": "published",
            },
        ]

        results = service.search_articles("fastapi")

        assert len(results) == 1

    def test_결과_없음(self) -> None:
        """매칭되는 문서가 없으면 빈 리스트를 반환한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_many.return_value = [
            {"title": "React 가이드", "tags": ["frontend"], "content": ""},
        ]

        results = service.search_articles("django")

        assert len(results) == 0

    def test_포털검색은_공개_게시문서만_반환한다(self) -> None:
        """포털 검색은 공개(public)+게시(published) 문서만 노출한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_many.return_value = [
            {
                "_id": "KA-001",
                "title": "비밀번호 재설정",
                "tags": ["faq"],
                "content": "계정 설정에서 재설정합니다.",
                "status": "published",
                "visibility": "public",
            },
            {
                "_id": "KA-002",
                "title": "내부 운영 체크리스트",
                "tags": ["ops"],
                "content": "내부 전용",
                "status": "published",
                "visibility": "internal",
            },
            {
                "_id": "KA-003",
                "title": "공개 예정 문서",
                "tags": ["faq"],
                "content": "아직 초안",
                "status": "draft",
                "visibility": "public",
            },
        ]

        results = service.list_portal_articles(keyword="비밀번호")

        assert [article["_id"] for article in results] == ["KA-001"]

    def test_AI_답변_추천은_상위_문서를_점수순으로_반환한다(self) -> None:
        """AI 추천은 질문과 가장 가까운 공개 문서를 높은 점수 순으로 제안한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_many.return_value = [
            {
                "_id": "KA-001",
                "title": "비밀번호 재설정 방법",
                "summary": "로그인 문제 해결",
                "tags": ["계정", "보안"],
                "content": "비밀번호를 잊어버렸을 때 재설정 링크를 요청합니다.",
                "status": "published",
                "visibility": "public",
            },
            {
                "_id": "KA-002",
                "title": "2단계 인증 설정",
                "summary": "OTP 설정",
                "tags": ["보안"],
                "content": "앱에서 2단계 인증을 설정하는 방법입니다.",
                "status": "published",
                "visibility": "public",
            },
            {
                "_id": "KA-003",
                "title": "배송 일정 변경",
                "summary": "주문 관리",
                "tags": ["물류"],
                "content": "출고 일정을 변경하는 절차입니다.",
                "status": "published",
                "visibility": "public",
            },
        ]

        suggestions = service.suggest_articles("비밀번호를 잊어버렸어요", visibility="public")

        assert suggestions[0]["article_id"] == "KA-001"
        assert all(item["article_id"] != "KA-003" for item in suggestions)
        assert suggestions[0]["recommended_answer"]


class Test문서평가:
    """지식 문서 평가 테스트."""

    def test_첫_평가(self) -> None:
        """최초 평가 시 해당 평점을 그대로 적용한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_by_id.return_value = {
            "_id": "KA-0001",
            "helpfulness_rating": None,
            "views_count": 0,
        }

        result = service.rate_article("KA-0001", Decimal("4.5"))

        assert result["new_rating"] == "4.5"
        repo.update_by_id.assert_called_once()

    def test_문서_미존재(self) -> None:
        """문서가 없으면 에러를 반환한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_by_id.return_value = None

        result = service.rate_article("KA-9999", Decimal("5.0"))

        assert "error" in result

    def test_누적_평균(self) -> None:
        """기존 평점이 있으면 누적 평균으로 업데이트한다."""
        service, repo, _, _, _ = _make_service()
        repo.find_by_id.return_value = {
            "_id": "KA-0001",
            "helpfulness_rating": "4.0",
            "views_count": 3,
        }

        result = service.rate_article("KA-0001", Decimal("5.0"))

        assert result["new_rating"] == "4.25"


class Test포털피드백:
    """셀프서비스 포털 피드백 테스트."""

    def test_도움됨_피드백은_집계와_로그를_남긴다(self) -> None:
        """공개 문서에 대한 도움됨 피드백은 카운트와 피드백 로그를 함께 갱신한다."""
        service, article_repo, feedback_repo, _, _ = _make_service()
        article_repo.find_by_id.return_value = {
            "_id": "KA-0001",
            "status": "published",
            "visibility": "public",
            "helpful_count": 2,
            "not_helpful_count": 1,
        }

        result = service.submit_feedback(
            article_id="KA-0001",
            is_helpful=True,
            comment="도움이 되었습니다",
            user_id=None,
        )

        assert result["helpful_count"] == 3
        assert result["not_helpful_count"] == 1
        article_repo.update_by_id.assert_called_once_with(
            "KA-0001",
            {"helpful_count": 3, "not_helpful_count": 1},
        )
        feedback_repo.insert.assert_called_once()


class Test버전과리뷰주기:
    """버전 비교와 리뷰 주기 알림 테스트."""

    def test_문서_수정시_새_버전_스냅샷을_생성한다(self) -> None:
        """제목 또는 본문이 바뀌면 다음 버전 스냅샷이 저장된다."""
        service, article_repo, _, version_repo, _ = _make_service()
        article_repo.find_by_id.return_value = {
            "_id": "KA-001",
            "title": "기존 제목",
            "content": "첫 문단\n둘째 문단",
            "summary": "기존 요약",
            "category": "faq",
            "tags": ["보안"],
            "current_version": 1,
            "status": "published",
        }

        result = service.update_article(
            "KA-001",
            {
                "title": "변경된 제목",
                "content": "첫 문단\n둘째 문단\n추가 문단",
                "change_summary": "최신 절차 반영",
            },
            user_id="EMP-001",
        )

        assert result["current_version"] == 2
        article_repo.update_by_id.assert_called_once()
        version_repo.insert.assert_called_once()
        assert version_repo.insert.call_args.args[0]["version_number"] == 2
        assert version_repo.insert.call_args.args[0]["change_summary"] == "최신 절차 반영"

    def test_버전_diff는_라인별_변경사항을_반환한다(self) -> None:
        """버전 비교는 수정/추가 라인을 식별해 반환한다."""
        service, _, _, version_repo, _ = _make_service()
        version_repo.find_many.return_value = [
            {
                "article_id": "KA-001",
                "version_number": 1,
                "title": "비밀번호 재설정 방법",
                "content": "첫 줄\n둘째 줄",
            },
            {
                "article_id": "KA-001",
                "version_number": 2,
                "title": "비밀번호 재설정 가이드",
                "content": "첫 줄\n수정된 둘째 줄\n새 줄",
            },
        ]

        diff = service.get_version_diff("KA-001", from_version=1, to_version=2)

        assert diff["from_version"] == 1
        assert diff["to_version"] == 2
        assert any(change["type"] == "modify" for change in diff["changes"])
        assert any(change["type"] == "add" for change in diff["changes"])

    def test_리뷰_주기_점검은_만기_문서에_리마인더를_생성한다(self) -> None:
        """리뷰 주기가 지난 문서는 알림 로그가 남고 결과에 포함된다."""
        service, article_repo, _, _, reminder_repo = _make_service()
        now = datetime(2026, 4, 8, 13, 0, tzinfo=UTC)
        article_repo.find_many.return_value = [
            {
                "_id": "KA-001",
                "title": "분실 비밀번호 대응",
                "author": "EMP-001",
                "status": "published",
                "review_interval_days": 30,
                "last_reviewed_at": now - timedelta(days=45),
                "current_version": 3,
            },
            {
                "_id": "KA-002",
                "title": "최근 공지",
                "author": "EMP-002",
                "status": "published",
                "review_interval_days": 30,
                "last_reviewed_at": now - timedelta(days=10),
                "current_version": 1,
            },
        ]
        reminder_repo.find_many.return_value = []

        due_articles = service.run_review_due_check(now=now)

        assert [item["article_id"] for item in due_articles] == ["KA-001"]
        reminder_repo.insert.assert_called_once()
        assert reminder_repo.insert.call_args.args[0]["article_id"] == "KA-001"
