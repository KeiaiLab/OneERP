"""지식 문서 CRUD, 검색, 버전 비교, 공개 포털 라우트."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Request
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError, raise_not_found
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from ..models.knowledge_article import KnowledgeArticleCreate, KnowledgeArticleUpdate
from ..services.article_service import ArticleService

router = APIRouter(prefix="/api/v1/knowledge-articles", tags=["지식 문서"])
portal_router = APIRouter(prefix="/api/v1/portal", tags=["셀프서비스 포털"])


def _resolve_tenant_id(request: Request) -> str:
    """요청 헤더에서 테넌트 ID를 해석한다."""
    return request.headers.get("X-Tenant-Id", "default")


def _get_service_from_request(request: Request) -> ArticleService:
    return ArticleService(tenant_id=_resolve_tenant_id(request))


def _get_service_for_user(user: CurrentUserDep) -> ArticleService:
    return ArticleService(tenant_id=user.tenant_id)


class PortalFeedbackRequest(BaseModel):
    """포털 피드백 요청 스키마."""

    is_helpful: bool
    comment: str = ""


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("knowledge_article:create"))]
)
async def create_article(
    body: KnowledgeArticleCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """지식 문서를 생성한다."""
    service = _get_service_for_user(user)
    return service.create_article(body.model_dump(), user_id=user.sub)


@router.get("", dependencies=[Depends(require_permission("knowledge_article:read"))])
async def list_articles(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """지식 문서 목록을 페이지네이션으로 조회한다."""
    service = _get_service_for_user(user)
    return service.list_articles(page=page, page_size=page_size)


@router.get("/search", dependencies=[Depends(require_permission("knowledge_article:read"))])
async def search_articles(
    request: Request,
    keyword: str = "",
    visibility: str | None = None,
    *,
    ai_suggest: bool = False,
) -> dict[str, Any]:
    """지식 문서를 검색하고 필요 시 AI 추천 결과를 함께 반환한다."""
    service = _get_service_from_request(request)
    results = service.search_articles(keyword, visibility=visibility)
    ai_suggestions = service.suggest_articles(keyword, visibility=visibility) if ai_suggest else []
    return {"data": results, "total": len(results), "ai_suggestions": ai_suggestions}


@router.get(
    "/{article_id}/versions/diff",
    dependencies=[Depends(require_permission("knowledge_article:read"))],
)
async def get_version_diff(
    article_id: str,
    request: Request,
    from_version: int,
    to_version: int,
) -> dict[str, Any]:
    """두 버전의 변경 내역을 비교한다."""
    service = _get_service_from_request(request)
    try:
        return service.get_version_diff(
            article_id, from_version=from_version, to_version=to_version
        )
    except ValueError as exc:
        raise OneERPError(status_code=422, error="ERR-KNW-032", detail=str(exc)) from exc


@router.post(
    "/review-reminders/run",
    dependencies=[Depends(require_permission("knowledge_article:write"))],
)
async def run_review_due_check(request: Request) -> dict[str, Any]:
    """리뷰 주기가 지난 문서를 점검하고 알림 로그를 남긴다."""
    service = _get_service_from_request(request)
    due_articles = service.run_review_due_check()
    return {"data": due_articles, "total": len(due_articles)}


@router.post(
    "/{article_id}/review",
    dependencies=[Depends(require_permission("knowledge_article:write"))],
)
async def mark_article_reviewed(
    article_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """문서 리뷰 완료를 기록한다."""
    service = _get_service_for_user(user)
    try:
        return service.mark_reviewed(article_id, user_id=user.sub)
    except ValueError as exc:
        raise_not_found(str(exc))


@router.get("/{article_id}", dependencies=[Depends(require_permission("knowledge_article:read"))])
async def get_article(article_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """지식 문서를 단건 조회한다."""
    service = _get_service_for_user(user)
    article = service.get_article(article_id)
    if not article:
        raise_not_found("지식 문서를 찾을 수 없습니다")
    return cast("dict[str, Any]", article)


@router.put("/{article_id}", dependencies=[Depends(require_permission("knowledge_article:write"))])
async def update_article(
    article_id: str,
    body: KnowledgeArticleUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """지식 문서를 수정한다."""
    service = _get_service_for_user(user)
    try:
        return service.update_article(
            article_id, body.model_dump(exclude_none=True), user_id=user.sub
        )
    except ValueError as exc:
        raise_not_found(str(exc))


@router.delete(
    "/{article_id}",
    status_code=204,
    dependencies=[Depends(require_permission("knowledge_article:delete"))],
)
async def delete_article(article_id: str, user: CurrentUserDep) -> None:
    """지식 문서를 삭제한다."""
    service = _get_service_for_user(user)
    try:
        service.delete_article(article_id)
    except ValueError as exc:
        raise_not_found(str(exc))


@portal_router.get("/articles")
async def list_portal_articles(
    request: Request,
    keyword: str = "",
    category: str | None = None,
    tag: str | None = None,
) -> dict:
    """셀프서비스 포털용 공개 지식 문서를 조회한다."""
    service = _get_service_from_request(request)
    results = service.list_portal_articles(keyword=keyword, category=category, tag=tag)
    return {"data": results, "total": len(results)}


@portal_router.post("/articles/{article_id}/feedback")
async def submit_portal_feedback(
    request: Request,
    article_id: str,
    body: PortalFeedbackRequest,
) -> dict:
    """셀프서비스 포털에서 도움됨/도움안됨 피드백을 남긴다."""
    service = _get_service_from_request(request)
    result = service.submit_feedback(
        article_id=article_id,
        is_helpful=body.is_helpful,
        comment=body.comment,
        user_id=request.headers.get("X-Portal-User-Id") or request.headers.get("X-User-Sub"),
    )
    if "error" in result:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail=result["error"],
        )
    return result
