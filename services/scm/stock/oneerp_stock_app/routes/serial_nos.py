"""시리얼번호(SerialNo) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.serial_no import SerialNo, SerialNoCreate, SerialNoUpdate

router = APIRouter(prefix="/api/v1/serial-nos", tags=["시리얼번호"])

_COLLECTION = "serial_nos"
_PREFIX = "SN"


def _get_repo() -> Repository:
    """시리얼번호 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.post("", status_code=201, dependencies=[Depends(require_permission("serial_no:create"))])
def create_serial_no(body: SerialNoCreate) -> dict:
    """시리얼번호를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = SerialNo(
        serial_no=body.serial_no,
        item_code=body.item_code,
        item_name=body.item_name,
        status=body.status,
        warehouse=body.warehouse,
        purchase_date=body.purchase_date,
        delivery_date=body.delivery_date,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "시리얼번호가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("serial_no:read"))])
def list_serial_nos(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """시리얼번호 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("serial_no:read"))])
def get_serial_no(doc_id: str) -> dict:
    """시리얼번호를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="시리얼번호를 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("serial_no:write"))])
def update_serial_no(doc_id: str, body: SerialNoUpdate) -> dict:
    """시리얼번호를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="시리얼번호를 찾을 수 없습니다"
        )
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "시리얼번호가 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=200, dependencies=[Depends(require_permission("serial_no:delete"))]
)
def delete_serial_no(doc_id: str) -> dict:
    """시리얼번호를 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="시리얼번호를 찾을 수 없습니다"
        )
    repo.delete_by_id(doc_id)
    return {"id": doc_id, "message": "시리얼번호가 삭제되었습니다"}
