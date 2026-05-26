"""Knowledge 모델 단위 테스트."""

from __future__ import annotations

from oneerp_knowledge_app.models.faq import Faq, FaqCreate
from oneerp_knowledge_app.models.knowledge_article import KnowledgeArticle, KnowledgeArticleCreate
from oneerp_knowledge_app.models.knowledge_category import (
    KnowledgeCategory,
    KnowledgeCategoryCreate,
)


class Test지식문서모델:
    """KnowledgeArticle 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """KnowledgeArticleCreate 스키마가 올바르게 동작한다."""
        data = KnowledgeArticleCreate(
            title="FastAPI 시작 가이드",
            content="# FastAPI\n\n빠른 API 개발",
            category="KC-0001",
            author="EMP-001",
            tags=["python", "fastapi"],
        )
        assert data.title == "FastAPI 시작 가이드"
        assert data.tags is not None
        assert len(data.tags) == 2

    def test_문서_기본값(self) -> None:
        """KnowledgeArticle 문서의 기본값을 검증한다."""
        doc = KnowledgeArticle()
        assert doc.status == "draft"
        assert doc.views_count == 0


class Test지식분류모델:
    """KnowledgeCategory 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """KnowledgeCategoryCreate 스키마가 올바르게 동작한다."""
        data = KnowledgeCategoryCreate(
            category_name="개발 가이드",
            description="소프트웨어 개발 관련 문서",
        )
        assert data.category_name == "개발 가이드"

    def test_문서_기본값(self) -> None:
        """KnowledgeCategory 문서의 기본값을 검증한다."""
        doc = KnowledgeCategory()
        assert doc.sort_order == 0


class TestFaq모델:
    """FAQ 모델 테스트."""

    def test_생성_스키마(self) -> None:
        """FaqCreate 스키마가 올바르게 동작한다."""
        data = FaqCreate(
            question="비밀번호를 잊었습니다. 어떻게 하나요?",
            answer="비밀번호 찾기 페이지에서 재설정할 수 있습니다.",
        )
        assert data.question.startswith("비밀번호")

    def test_문서_기본값(self) -> None:
        """Faq 문서의 기본값을 검증한다."""
        doc = Faq()
        assert doc.status == "draft"
        assert doc.views_count == 0
