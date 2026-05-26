"""견적요청(RequestForQuotation) CRUD 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_buying_app.models.request_for_quotation import (
    RequestForQuotation,
    RequestForQuotationCreate,
    RequestForQuotationUpdate,
)

router = APIRouter(prefix="/api/v1/request-for-quotations", tags=["견적요청"])

_COLLECTION = "request_for_quotations"
_PREFIX = "RFQ"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("request_for_quotation:create"))]
)
def 견적요청_생성(body: RequestForQuotationCreate, user: CurrentUserDep) -> dict[str, Any]:
    """견적요청을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    rfq = RequestForQuotation(
        _id=doc_id,
        tenant_id=user.tenant_id,
        transaction_date=body.transaction_date,
        suppliers=body.suppliers,
        items=body.items,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(rfq)
    return {"id": doc_id, "message": "견적요청이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("request_for_quotation:read"))])
def 견적요청_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """견적요청 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("request_for_quotation:read"))])
def 견적요청_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """견적요청 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적요청을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("request_for_quotation:write"))])
def 견적요청_수정(
    doc_id: str,
    body: RequestForQuotationUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """견적요청을 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적요청을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "견적요청이 수정되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("request_for_quotation:submit"))]
)
def 견적요청_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """견적요청을 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적요청을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    repo.submit_with_event(
        doc_id, event_type=EventType.REQUEST_FOR_QUOTATION_SUBMITTED, triggered_by=user.sub
    )
    return {"id": doc_id, "message": "견적요청이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("request_for_quotation:cancel"))]
)
def 견적요청_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """견적요청을 취소한다 (제출 → 취소)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적요청을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")

    repo.cancel(doc_id)
    return {"id": doc_id, "message": "견적요청이 취소되었습니다"}
