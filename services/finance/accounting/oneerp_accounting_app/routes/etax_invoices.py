"""전자세금계산서(E-Tax Invoice) CRUD 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import get_or_404

from ..models.etax_invoice import (
    ETaxInvoice,
    ETaxInvoiceCreate,
    ETaxInvoiceUpdate,
    NTSCancelRequest,
)
from ..services.etax_service import ETaxService, ETaxServiceError
from ..services.nts_api_client import create_nts_client

router = APIRouter(prefix="/api/v1/etax-invoices", tags=["전자세금계산서"])

_COLLECTION = "etax_invoices"
_PREFIX = "ETAX"
_NOT_FOUND = "전자세금계산서를 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("etax_invoice:create"))])
def 전자세금계산서_생성(body: ETaxInvoiceCreate, user: CurrentUserDep) -> dict:
    """전자세금계산서를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    etax = ETaxInvoice(
        _id=doc_id,
        tenant_id=user.tenant_id,
        invoice_ref=body.invoice_ref,
        issue_date=body.issue_date,
        supplier_or_customer=body.supplier_or_customer,
        supply_amount=body.supply_amount,
        tax_amount=body.tax_amount,
        nts_confirmation_no=body.nts_confirmation_no,
        transmission_status=body.transmission_status,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(etax)
    return {"id": doc_id, "message": "전자세금계산서 생성 완료"}


@router.get("", dependencies=[Depends(require_permission("etax_invoice:read"))])
def 전자세금계산서_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """전자세금계산서 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("etax_invoice:read"))])
def 전자세금계산서_조회(doc_id: str, user: CurrentUserDep) -> dict:
    """전자세금계산서를 조회한다."""
    repo = _get_repo(user.tenant_id)
    return get_or_404(repo, doc_id, _NOT_FOUND)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("etax_invoice:write"))])
def 전자세금계산서_수정(doc_id: str, body: ETaxInvoiceUpdate, user: CurrentUserDep) -> dict:
    """전자세금계산서를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {**doc, **update_data}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("etax_invoice:submit"))])
def 전자세금계산서_제출(doc_id: str, user: CurrentUserDep) -> dict:
    """전자세금계산서를 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    repo.submit_with_event(
        doc_id,
        event_type=EventType.ETAX_INVOICE_SUBMITTED,
        triggered_by=user.sub,
    )
    return {**doc, "docstatus": DocStatus.SUBMITTED}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("etax_invoice:delete"))]
)
def 전자세금계산서_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """전자세금계산서를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    get_or_404(repo, doc_id, _NOT_FOUND)
    repo.delete_by_id(doc_id)


# ---------------------------------------------------------------------------
# 국세청 API 연동 커스텀 라우트
# ---------------------------------------------------------------------------


def _get_etax_service(tenant_id: str) -> ETaxService:
    """테넌트 기반 ETaxService를 생성한다."""
    nts_client = create_nts_client()
    return ETaxService(nts_client=nts_client, tenant_id=tenant_id)


@router.post(
    "/{doc_id}/submit-to-nts",
    dependencies=[Depends(require_permission("etax_invoice:submit"))],
)
async def 국세청_전송(doc_id: str, user: CurrentUserDep) -> dict:
    """전자세금계산서를 국세청에 전송한다."""
    service = _get_etax_service(user.tenant_id)
    try:
        result = await service.submit_to_nts(doc_id)
    except ETaxServiceError as e:
        raise_bad_request(str(e))
    return result


@router.get(
    "/{doc_id}/nts-status",
    dependencies=[Depends(require_permission("etax_invoice:read"))],
)
async def 국세청_상태_조회(doc_id: str, user: CurrentUserDep) -> dict:
    """국세청 전송 상태를 조회한다."""
    service = _get_etax_service(user.tenant_id)
    try:
        result = await service.check_nts_status(doc_id)
    except ETaxServiceError as e:
        raise_bad_request(str(e))
    return result


@router.post(
    "/{doc_id}/cancel-nts",
    dependencies=[Depends(require_permission("etax_invoice:submit"))],
)
async def 국세청_취소(doc_id: str, body: NTSCancelRequest, user: CurrentUserDep) -> dict:
    """국세청 전송을 취소한다."""
    service = _get_etax_service(user.tenant_id)
    try:
        result = await service.cancel_nts(doc_id, body.reason)
    except ETaxServiceError as e:
        raise_bad_request(str(e))
    return result
