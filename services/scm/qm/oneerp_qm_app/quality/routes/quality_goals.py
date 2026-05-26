"""품질목표(QualityGoal) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.quality_goal import QualityGoal, QualityGoalCreate, QualityGoalUpdate

router = APIRouter(prefix="/api/v1/quality-goals", tags=["품질목표"])
_COLLECTION = "quality_goals"
_PREFIX = "QGOL"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("quality_goal:create"))]
)
async def create_quality_goal(body: QualityGoalCreate) -> dict:
    """품질목표를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = QualityGoal(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"quality_goal_id": doc_id, "message": "품질목표가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("quality_goal:read"))])
async def list_quality_goals(page: int = 1, page_size: int = 20) -> dict:
    """품질목표 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("quality_goal:read"))])
async def get_quality_goal(doc_id: str) -> dict:
    """품질목표 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="품질목표를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("quality_goal:write"))])
async def update_quality_goal(doc_id: str, body: QualityGoalUpdate) -> dict:
    """품질목표를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="품질목표를 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "품질목표가 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("quality_goal:delete"))])
async def delete_quality_goal(doc_id: str) -> dict:
    """품질목표를 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="품질목표를 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "품질목표가 삭제되었습니다"}
