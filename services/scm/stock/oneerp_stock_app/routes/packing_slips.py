"""포장전표(PackingSlip) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.packing_slip import PackingSlip, PackingSlipCreate, PackingSlipUpdate

router = APIRouter(prefix="/api/v1/packing-slips", tags=["포장전표"])

_COLLECTION = "packing_slips"
_PREFIX = "PS"


def _get_repo() -> Repository:
    """포장전표 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.post("", status_code=201, dependencies=[Depends(require_permission("packing_slip:create"))])
def create_packing_slip(body: PackingSlipCreate) -> dict:
    """포장전표를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = PackingSlip(
        delivery_note=body.delivery_note,
        items=body.items,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "포장전표가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("packing_slip:read"))])
def list_packing_slips(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """포장전표 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("packing_slip:read"))])
def get_packing_slip(doc_id: str) -> dict:
    """포장전표를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="포장전표를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("packing_slip:write"))])
def update_packing_slip(doc_id: str, body: PackingSlipUpdate) -> dict:
    """포장전표를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="포장전표를 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "포장전표가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("packing_slip:submit"))])
def submit_packing_slip(doc_id: str, user: CurrentUserDep) -> dict:
    """포장전표를 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="포장전표를 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400, error="invalid_status", detail="초안 상태에서만 제출 가능"
        )
    repo.submit_with_event(
        doc_id,
        event_type=EventType.PACKING_SLIP_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"message": "포장전표가 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("packing_slip:cancel"))])
def cancel_packing_slip(doc_id: str) -> dict:
    """포장전표를 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="포장전표를 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(status_code=400, error="invalid_status", detail="제출된 문서만 취소 가능")
    repo.cancel(doc_id)
    return {"message": "포장전표가 취소되었습니다"}
