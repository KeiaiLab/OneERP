"""POS 영수증(POSReceipt) 로그 라우터 — 생성/조회만 제공."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_selling_app.models.pos_receipt import POSReceipt, POSReceiptCreate

router = APIRouter(prefix="/api/v1/pos-receipts", tags=["POS 영수증"])

_COLLECTION = "pos_receipts"
_PREFIX = "POSR"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("pos_receipt:create"))])
def POS영수증_생성(body: POSReceiptCreate, user: CurrentUserDep) -> dict:
    """POS 영수증 로그를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    doc = POSReceipt(
        _id=doc_id,
        tenant_id=user.tenant_id,
        transaction_id=body.transaction_id,
        receipt_data=body.receipt_data,
        printed_at=body.printed_at,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)
    return {"id": doc_id, "message": "POS 영수증이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("pos_receipt:read"))])
def POS영수증_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """POS 영수증 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count()
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("pos_receipt:read"))])
def POS영수증_조회(doc_id: str, user: CurrentUserDep) -> dict:
    """POS 영수증 상세를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("POS 영수증을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc
