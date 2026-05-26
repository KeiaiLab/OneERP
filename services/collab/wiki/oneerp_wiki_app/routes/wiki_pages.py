"""위키 페이지(WikiPage) 커스텀 API 라우터 — 발행/보관 워크플로."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request
from oneerp_core.permissions import require_permission

from oneerp_wiki_app.models.wiki_page import WikiPageStatus
from oneerp_wiki_app.services.wiki_page_service import WikiPageService

router = APIRouter(prefix="/api/v1/wiki-pages", tags=["위키페이지"])


def _get_service(tenant_id: str) -> WikiPageService:
    """현재 사용자의 tenant에 바인딩된 WikiPageService를 반환한다."""
    return WikiPageService(tenant_id=tenant_id)


@router.post(
    "/{doc_id}/publish",
    dependencies=[Depends(require_permission("wiki_page:create"))],
)
def publish_page(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """위키 페이지를 발행한다."""
    service = _get_service(user.tenant_id)
    doc = service.get_page(doc_id)
    if doc.get("status") != WikiPageStatus.DRAFT:
        raise_bad_request("초안 상태의 페이지만 발행할 수 있습니다")

    return service.publish_page(doc_id, editor_id=user.sub)


@router.post(
    "/{doc_id}/archive",
    dependencies=[Depends(require_permission("wiki_page:create"))],
)
def archive_page(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """위키 페이지를 보관 처리한다."""
    service = _get_service(user.tenant_id)
    doc = service.get_page(doc_id)
    if doc.get("status") != WikiPageStatus.PUBLISHED:
        raise_bad_request("발행된 페이지만 보관할 수 있습니다")

    return service.archive_page(doc_id, editor_id=user.sub)


@router.get(
    "/tree/{space_id}",
    dependencies=[Depends(require_permission("wiki_page:read"))],
)
def get_page_tree(space_id: str, user: CurrentUserDep) -> list[dict[str, Any]]:
    """위키 공간의 페이지 트리를 조회한다."""
    service = _get_service(user.tenant_id)
    return service.get_page_tree(space_id)
