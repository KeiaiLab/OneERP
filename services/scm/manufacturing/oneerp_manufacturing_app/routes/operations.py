"""공정(Operation) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.operation import Operation, OperationCreate, OperationUpdate

router = APIRouter(prefix="/api/v1/operations", tags=["공정"])

_COLLECTION = "operations"
_PREFIX = "OPR"


def _get_repo() -> Repository:
    """공정 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.post("", status_code=201, dependencies=[Depends(require_permission("operation:create"))])
def create_operation(body: OperationCreate) -> dict:
    """공정을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = Operation(
        operation_name=body.operation_name,
        workstation=body.workstation,
        time_in_mins=body.time_in_mins,
        description=body.description,
        is_active=body.is_active,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "공정이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("operation:read"))])
def list_operations(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """공정 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("operation:read"))])
def get_operation(doc_id: str) -> dict:
    """공정을 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="공정을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("operation:write"))])
def update_operation(doc_id: str, body: OperationUpdate) -> dict:
    """공정을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="공정을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "공정이 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=200, dependencies=[Depends(require_permission("operation:delete"))]
)
def delete_operation(doc_id: str) -> dict:
    """공정을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="공정을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"id": doc_id, "message": "공정이 삭제되었습니다"}
