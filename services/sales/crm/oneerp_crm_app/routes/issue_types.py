"""이슈유형(IssueType) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.issue_type import IssueType, IssueTypeCreate, IssueTypeUpdate

router = APIRouter(prefix="/api/v1/issue-types", tags=["이슈유형"])
_COLLECTION = "issue_types"
_PREFIX = "ISTP"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post("/", status_code=201, dependencies=[Depends(require_permission("issue_type:create"))])
async def create_issue_type(body: IssueTypeCreate) -> dict:
    """이슈유형을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = IssueType(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"issue_type_id": doc_id, "message": "이슈유형이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("issue_type:read"))])
async def list_issue_types(page: int = 1, page_size: int = 20) -> dict:
    """이슈유형 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("issue_type:read"))])
async def get_issue_type(doc_id: str) -> dict:
    """이슈유형 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="이슈유형을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("issue_type:write"))])
async def update_issue_type(doc_id: str, body: IssueTypeUpdate) -> dict:
    """이슈유형을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="이슈유형을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "이슈유형이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("issue_type:delete"))])
async def delete_issue_type(doc_id: str) -> dict:
    """이슈유형을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="이슈유형을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "이슈유형이 삭제되었습니다"}
