"""지식 문서(KnowledgeArticle) 문서 모델."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ArticleStatus(StrEnum):
    """지식 문서 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ArticleVisibility(StrEnum):
    """지식 문서 공개 범위."""

    INTERNAL = "internal"
    PUBLIC = "public"


class KnowledgeArticleCreate(BaseModel):
    """지식 문서 생성 요청 스키마."""

    title: str
    content: str
    summary: str = ""
    category: str
    author: str
    tags: list[str] | None = None
    status: ArticleStatus = ArticleStatus.DRAFT
    visibility: ArticleVisibility = ArticleVisibility.INTERNAL
    review_interval_days: int = 90
    last_reviewed_at: datetime | None = None
    views_count: int = 0
    helpfulness_rating: Decimal | None = None
    helpful_count: int = 0
    not_helpful_count: int = 0


class KnowledgeArticleUpdate(BaseModel):
    """지식 문서 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    summary: str | None = None
    category: str | None = None
    author: str | None = None
    tags: list[str] | None = None
    status: ArticleStatus | None = None
    visibility: ArticleVisibility | None = None
    review_interval_days: int | None = None
    last_reviewed_at: datetime | None = None
    change_summary: str | None = None
    views_count: int | None = None
    helpfulness_rating: Decimal | None = None
    helpful_count: int | None = None
    not_helpful_count: int | None = None


class KnowledgeArticle(BaseDocument):
    """지식 문서."""

    title: str = ""
    content: str = ""
    summary: str = ""
    category: str = ""
    author: str = ""
    tags: list[str] | None = None
    status: ArticleStatus = ArticleStatus.DRAFT
    visibility: ArticleVisibility = ArticleVisibility.INTERNAL
    current_version: int = 1
    review_interval_days: int = 90
    last_reviewed_at: datetime | None = None
    last_reviewed_by: str = ""
    published_at: datetime | None = None
    views_count: int = 0
    helpfulness_rating: Decimal | None = None
    helpful_count: int = 0
    not_helpful_count: int = 0
