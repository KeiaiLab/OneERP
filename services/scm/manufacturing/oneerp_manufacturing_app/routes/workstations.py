"""작업장(Workstation) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.workstation import Workstation, WorkstationCreate, WorkstationUpdate

router = APIRouter(prefix="/api/v1/workstations", tags=["작업장"])

_COLLECTION = "workstations"
_PREFIX = "WS"


def _get_repo() -> Repository:
    """작업장 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.post("", status_code=201, dependencies=[Depends(require_permission("workstation:create"))])
def create_workstation(body: WorkstationCreate) -> dict:
    """작업장을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = Workstation(
        workstation_name=body.workstation_name,
        production_capacity=body.production_capacity,
        hourly_rate=body.hourly_rate,
        is_active=body.is_active,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "작업장이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("workstation:read"))])
def list_workstations(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """작업장 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("workstation:read"))])
def get_workstation(doc_id: str) -> dict:
    """작업장을 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업장을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("workstation:write"))])
def update_workstation(doc_id: str, body: WorkstationUpdate) -> dict:
    """작업장을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업장을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "작업장이 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=200, dependencies=[Depends(require_permission("workstation:delete"))]
)
def delete_workstation(doc_id: str) -> dict:
    """작업장을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업장을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"id": doc_id, "message": "작업장이 삭제되었습니다"}
