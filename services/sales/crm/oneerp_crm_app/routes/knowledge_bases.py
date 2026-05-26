"""지식베이스(KnowledgeBase) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["지식베이스"])
_COLLECTION = "knowledge_bases"
_PREFIX = "KB"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("knowledge_bas:create"))]
)
async def create_knowledge_base(body: KnowledgeBaseCreate) -> dict:
    """지식베이스를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = KnowledgeBase(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"knowledge_base_id": doc_id, "message": "지식베이스가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("knowledge_bas:read"))])
async def list_knowledge_bases(page: int = 1, page_size: int = 20) -> dict:
    """지식베이스 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("knowledge_bas:read"))])
async def get_knowledge_base(doc_id: str) -> dict:
    """지식베이스 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="지식베이스를 찾을 수 없습니다",
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("knowledge_bas:write"))])
async def update_knowledge_base(doc_id: str, body: KnowledgeBaseUpdate) -> dict:
    """지식베이스를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="지식베이스를 찾을 수 없습니다",
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "지식베이스가 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("knowledge_bas:delete"))])
async def delete_knowledge_base(doc_id: str) -> dict:
    """지식베이스를 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="지식베이스를 찾을 수 없습니다",
        )
    repo.delete_by_id(doc_id)
    return {"message": "지식베이스가 삭제되었습니다"}
