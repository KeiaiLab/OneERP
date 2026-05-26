"""지식 문서 서비스 — 검색, 버전 비교, 리뷰 주기 알림 로직."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")
_VERSIONED_FIELDS = ("title", "content", "summary", "category", "tags", "visibility", "status")


class ArticleService:
    """지식 문서 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._article_repo = Repository("knowledge_articles", tenant_id=tenant_id)
        self._feedback_repo = Repository("knowledge_article_feedback", tenant_id=tenant_id)
        self._version_repo = Repository("knowledge_article_versions", tenant_id=tenant_id)
        self._review_notice_repo = Repository(
            "knowledge_article_review_notifications",
            tenant_id=tenant_id,
        )

    def list_articles(self, *, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """지식 문서 목록을 페이지네이션으로 조회한다."""
        skip = (page - 1) * page_size
        docs = self._article_repo.find_many(
            skip=skip,
            limit=page_size,
            sort=[("created_at", -1)],
        )
        return {
            "data": docs,
            "total": self._article_repo.count(),
            "page": page,
            "page_size": page_size,
        }

    def create_article(self, data: dict[str, Any], *, user_id: str) -> dict[str, Any]:
        """지식 문서를 생성하고 초기 버전 스냅샷을 남긴다."""
        now = datetime.now(tz=UTC)
        doc_id = generate_name("KA", tenant_id=self._tenant_id)
        status = data.get("status", "draft")
        article = {
            "_id": doc_id,
            "title": data["title"],
            "content": data["content"],
            "summary": data.get("summary", ""),
            "category": data.get("category", ""),
            "author": data["author"],
            "tags": data.get("tags") or [],
            "status": status,
            "visibility": data.get("visibility", "internal"),
            "current_version": 1,
            "review_interval_days": int(data.get("review_interval_days") or 90),
            "last_reviewed_at": data.get("last_reviewed_at")
            or (now if status == "published" else None),
            "last_reviewed_by": user_id if status == "published" else "",
            "published_at": now if status == "published" else None,
            "views_count": int(data.get("views_count") or 0),
            "helpfulness_rating": data.get("helpfulness_rating"),
            "helpful_count": int(data.get("helpful_count") or 0),
            "not_helpful_count": int(data.get("not_helpful_count") or 0),
            "created_by": user_id,
            "updated_by": user_id,
        }
        self._article_repo.insert(article)
        self._record_version_snapshot(
            article,
            version_number=1,
            change_summary="초기 생성",
            user_id=user_id,
        )
        return article

    def get_article(self, article_id: str) -> dict[str, Any] | None:
        """지식 문서 단건을 조회한다."""
        return self._article_repo.find_by_id(article_id)

    def update_article(
        self, article_id: str, updates: dict[str, Any], *, user_id: str
    ) -> dict[str, Any]:
        """지식 문서를 수정하고 변경분이 있으면 버전 스냅샷을 남긴다."""
        article = self._article_repo.find_by_id(article_id)
        if not article:
            msg = "지식 문서를 찾을 수 없습니다"
            raise ValueError(msg)

        update_data = dict(updates)
        change_summary = update_data.pop("change_summary", "") or "문서 수정"
        next_version = int(article.get("current_version") or 1)
        should_snapshot = any(
            field in update_data and update_data[field] != article.get(field)
            for field in _VERSIONED_FIELDS
        )
        if should_snapshot:
            self._ensure_baseline_version(article, user_id=user_id)
            next_version += 1
            update_data["current_version"] = next_version

        if update_data.get("status") == "published" and not article.get("published_at"):
            now = datetime.now(tz=UTC)
            update_data.setdefault("published_at", now)
            update_data.setdefault("last_reviewed_at", now)
            update_data.setdefault("last_reviewed_by", user_id)

        if update_data.get("last_reviewed_at") is not None:
            update_data.setdefault("last_reviewed_by", user_id)

        update_data["updated_by"] = user_id
        self._article_repo.update_by_id(article_id, update_data)
        updated = {**article, **update_data}

        if should_snapshot:
            self._record_version_snapshot(
                updated,
                version_number=next_version,
                change_summary=change_summary,
                user_id=user_id,
            )
        return updated

    def delete_article(self, article_id: str) -> None:
        """지식 문서를 삭제한다."""
        article = self._article_repo.find_by_id(article_id)
        if not article:
            msg = "지식 문서를 찾을 수 없습니다"
            raise ValueError(msg)
        self._article_repo.delete_by_id(article_id)

    def search_articles(
        self,
        keyword: str,
        *,
        visibility: str | None = None,
    ) -> list[dict[str, Any]]:
        """키워드로 게시된 지식 문서를 검색한다."""
        query: dict[str, Any] = {"status": "published"}
        if visibility:
            query["visibility"] = visibility

        all_articles = self._article_repo.find_many(query=query, limit=1000)
        results = []
        keyword_lower = keyword.lower().strip()
        for article in all_articles:
            title = article.get("title", "").lower()
            tags = article.get("tags") or []
            tags_text = " ".join(tag.lower() for tag in tags)
            content = article.get("content", "").lower()
            summary = article.get("summary", "").lower()
            if (
                not keyword_lower
                or keyword_lower in title
                or keyword_lower in tags_text
                or keyword_lower in content
                or keyword_lower in summary
            ):
                results.append(article)

        logger.info("지식 문서 검색: keyword=%s result=%d", keyword, len(results))
        return results

    def suggest_articles(
        self,
        keyword: str,
        *,
        visibility: str | None = None,
    ) -> list[dict[str, Any]]:
        """질문과 가장 가까운 지식 문서를 AI 추천 형식으로 반환한다."""
        if not keyword.strip():
            return []

        articles = self._article_repo.find_many(
            query={"status": "published", **({"visibility": visibility} if visibility else {})},
            limit=1000,
        )
        query_tokens = _tokenize(keyword)
        suggestions: list[dict[str, Any]] = []
        for article in articles:
            title = article.get("title", "")
            summary = article.get("summary", "")
            content = article.get("content", "")
            tags = article.get("tags") or []
            searchable = "\n".join([title, summary, " ".join(tags), content])
            score = _score_similarity(keyword, query_tokens, title, summary, searchable)
            if score < 0.1:
                continue
            suggestions.append(
                {
                    "article_id": article.get("_id"),
                    "title": title,
                    "summary": summary,
                    "score": round(score, 4),
                    "recommended_answer": summary or _excerpt(content),
                }
            )

        suggestions.sort(key=lambda item: (-item["score"], item["title"]))
        return suggestions[:5]

    def list_portal_articles(
        self,
        *,
        keyword: str = "",
        category: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        """셀프서비스 포털에서 노출할 공개 지식 문서를 검색한다."""
        articles = self.search_articles(keyword, visibility="public")
        results: list[dict[str, Any]] = []
        for article in articles:
            article_category = article.get("category")
            article_tags = article.get("tags") or []
            if category and article_category != category:
                continue
            if tag and tag not in article_tags:
                continue
            results.append(article)

        logger.info(
            "포털 지식 검색: keyword=%s category=%s tag=%s result=%d",
            keyword,
            category,
            tag,
            len(results),
        )
        return results

    def list_versions(self, article_id: str) -> list[dict[str, Any]]:
        """아티클 버전 목록을 조회한다."""
        return self._version_repo.find_many(
            {"article_id": article_id},
            limit=200,
            sort=[("version_number", 1)],
        )

    def get_version_diff(
        self,
        article_id: str,
        *,
        from_version: int,
        to_version: int,
    ) -> dict[str, Any]:
        """두 버전의 제목+본문을 비교해 라인 단위 변경을 반환한다."""
        versions = {doc.get("version_number"): doc for doc in self.list_versions(article_id)}
        article = self._article_repo.find_by_id(article_id)
        if article and int(article.get("current_version") or 1) not in versions:
            versions[int(article.get("current_version") or 1)] = article

        before = versions.get(from_version)
        after = versions.get(to_version)
        if before is None or after is None:
            msg = f"버전 {from_version if before is None else to_version}가 존재하지 않습니다"
            raise ValueError(msg)

        before_lines = _version_lines(before)
        after_lines = _version_lines(after)
        changes: list[dict[str, Any]] = []
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, before_lines, after_lines).get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace":
                max_len = max(i2 - i1, j2 - j1)
                for offset in range(max_len):
                    old_text = before_lines[i1 + offset] if i1 + offset < i2 else ""
                    new_text = after_lines[j1 + offset] if j1 + offset < j2 else ""
                    change_type = (
                        "modify" if old_text and new_text else ("remove" if old_text else "add")
                    )
                    line = j1 + offset + 1 if new_text else i1 + offset + 1
                    changes.append(
                        {
                            "type": change_type,
                            "line": line,
                            "old_text": old_text,
                            "new_text": new_text,
                        }
                    )
            elif tag == "delete":
                for offset, old_text in enumerate(before_lines[i1:i2], start=i1 + 1):
                    changes.append(
                        {
                            "type": "remove",
                            "line": offset,
                            "old_text": old_text,
                            "new_text": "",
                        }
                    )
            elif tag == "insert":
                for offset, new_text in enumerate(after_lines[j1:j2], start=j1 + 1):
                    changes.append(
                        {
                            "type": "add",
                            "line": offset,
                            "old_text": "",
                            "new_text": new_text,
                        }
                    )

        return {
            "article_id": article_id,
            "from_version": from_version,
            "to_version": to_version,
            "changes": changes,
        }

    def mark_reviewed(self, article_id: str, *, user_id: str) -> dict[str, Any]:
        """아티클 리뷰 완료 시각을 갱신한다."""
        article = self._article_repo.find_by_id(article_id)
        if not article:
            msg = "지식 문서를 찾을 수 없습니다"
            raise ValueError(msg)
        reviewed_at = datetime.now(tz=UTC)
        self._article_repo.update_by_id(
            article_id,
            {
                "last_reviewed_at": reviewed_at,
                "last_reviewed_by": user_id,
                "updated_by": user_id,
            },
        )
        return {
            "article_id": article_id,
            "last_reviewed_at": reviewed_at,
            "last_reviewed_by": user_id,
        }

    def run_review_due_check(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        """리뷰 주기가 지난 게시 문서를 찾아 알림 로그를 남긴다."""
        current = now or datetime.now(tz=UTC)
        articles = self._article_repo.find_many({"status": "published"}, limit=1000)
        due_articles: list[dict[str, Any]] = []
        for article in articles:
            reviewed_at = _as_datetime(
                article.get("last_reviewed_at")
                or article.get("published_at")
                or article.get("updated_at")
                or article.get("created_at")
            )
            if reviewed_at is None:
                continue
            review_interval_days = int(article.get("review_interval_days") or 90)
            days_since_review = (current - reviewed_at).days
            if days_since_review < review_interval_days:
                continue

            due_info = {
                "article_id": article.get("_id"),
                "title": article.get("title", ""),
                "author": article.get("author", ""),
                "current_version": int(article.get("current_version") or 1),
                "days_since_review": days_since_review,
                "review_interval_days": review_interval_days,
            }
            reminder_query = {
                "article_id": due_info["article_id"],
                "version_number": due_info["current_version"],
                "reminder_date": current.date().isoformat(),
            }
            existing = self._review_notice_repo.find_many(reminder_query, limit=1)
            if not existing:
                self._review_notice_repo.insert(
                    {
                        "_id": generate_name("KRN", tenant_id=self._tenant_id),
                        **reminder_query,
                        "author": due_info["author"],
                        "created_at": current,
                    }
                )
            due_articles.append(due_info)

        return due_articles

    def rate_article(self, article_id: str, rating: Decimal) -> dict[str, Any]:
        """지식 문서의 유용성을 평가한다."""
        article = self._article_repo.find_by_id(article_id)
        if not article:
            return {"error": "지식 문서를 찾을 수 없습니다"}

        current_rating = Decimal(str(article.get("helpfulness_rating") or 0))
        views = article.get("views_count", 0)
        if views > 0 and current_rating > 0:
            new_rating = (current_rating * views + rating) / (views + 1)
        else:
            new_rating = rating

        self._article_repo.update_by_id(
            article_id,
            {
                "helpfulness_rating": str(new_rating),
                "views_count": views + 1,
            },
        )
        return {
            "article_id": article_id,
            "previous_rating": str(current_rating),
            "new_rating": str(new_rating),
            "total_views": views + 1,
        }

    def submit_feedback(
        self,
        *,
        article_id: str,
        is_helpful: bool,
        comment: str = "",
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """공개 지식 문서에 도움됨/도움안됨 피드백을 기록한다."""
        article = self._article_repo.find_by_id(article_id)
        if not article:
            return {"error": "지식 문서를 찾을 수 없습니다"}
        if article.get("status") != "published" or article.get("visibility") != "public":
            return {"error": "공개 지식 문서를 찾을 수 없습니다"}

        helpful_count = int(article.get("helpful_count") or 0)
        not_helpful_count = int(article.get("not_helpful_count") or 0)
        if is_helpful:
            helpful_count += 1
        else:
            not_helpful_count += 1

        self._article_repo.update_by_id(
            article_id,
            {
                "helpful_count": helpful_count,
                "not_helpful_count": not_helpful_count,
            },
        )
        self._feedback_repo.insert(
            {
                "_id": generate_name("KBF", tenant_id=self._tenant_id),
                "article_id": article_id,
                "user_id": user_id,
                "is_helpful": is_helpful,
                "comment": comment,
                "created_at": datetime.now(tz=UTC),
            },
        )
        return {
            "article_id": article_id,
            "helpful_count": helpful_count,
            "not_helpful_count": not_helpful_count,
        }

    def _ensure_baseline_version(self, article: dict[str, Any], *, user_id: str) -> None:
        version_number = int(article.get("current_version") or 1)
        existing = self._version_repo.find_many(
            {"article_id": article.get("_id"), "version_number": version_number},
            limit=1,
        )
        if existing:
            return
        self._record_version_snapshot(
            article,
            version_number=version_number,
            change_summary="기준 버전 백필",
            user_id=user_id,
        )

    def _record_version_snapshot(
        self,
        article: dict[str, Any],
        *,
        version_number: int,
        change_summary: str,
        user_id: str,
    ) -> None:
        self._version_repo.insert(
            {
                "_id": generate_name("KAV", tenant_id=self._tenant_id),
                "article_id": article.get("_id"),
                "version_number": version_number,
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "summary": article.get("summary", ""),
                "category": article.get("category", ""),
                "tags": article.get("tags") or [],
                "visibility": article.get("visibility", "internal"),
                "status": article.get("status", "draft"),
                "change_summary": change_summary,
                "created_by": user_id,
                "created_at": datetime.now(tz=UTC),
            }
        )


def _excerpt(content: str, *, max_length: int = 160) -> str:
    text = " ".join(line.strip() for line in content.splitlines() if line.strip())
    return text[:max_length]


def _tokenize(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_RE.finditer(text)}


def _score_similarity(
    keyword: str,
    query_tokens: set[str],
    title: str,
    summary: str,
    searchable: str,
) -> float:
    searchable_lower = searchable.lower()
    title_tokens = _tokenize(title)
    searchable_tokens = _tokenize(searchable)
    overlap = len(query_tokens & searchable_tokens) / max(len(query_tokens), 1)
    title_overlap = len(query_tokens & title_tokens) / max(len(query_tokens), 1)
    exact_bonus = 1.0 if keyword.lower() in searchable_lower else 0.0
    fuzzy = max(
        SequenceMatcher(None, keyword.lower(), title.lower()).ratio(),
        SequenceMatcher(None, keyword.lower(), summary.lower()).ratio(),
        SequenceMatcher(None, keyword.lower(), searchable_lower[:300]).ratio(),
    )
    return min(1.0, overlap * 0.45 + title_overlap * 0.25 + fuzzy * 0.2 + exact_bonus * 0.1)


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str) and value:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


def _version_lines(document: dict[str, Any]) -> list[str]:
    title = document.get("title", "")
    content = document.get("content", "")
    return [f"# {title}", *content.splitlines()]
