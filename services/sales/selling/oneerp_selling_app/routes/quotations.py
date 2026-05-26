"""견적서(Quotation) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Response
from oneerp_core.config import get_core_settings
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_selling_app.models.quotation import (
    Quotation,
    QuotationCreate,
    QuotationItem,
    QuotationPortalSignRequest,
    QuotationSendEmailRequest,
    QuotationUpdate,
)
from oneerp_selling_app.services.price_list_service import PriceListService
from oneerp_selling_app.services.quotation_conversion_service import QuotationConversionService
from oneerp_selling_app.services.quotation_delivery_service import QuotationDeliveryService

router = APIRouter(prefix="/api/v1/quotations", tags=["견적서"])
portal_router = APIRouter(prefix="/api/v1/portal/quotations", tags=["견적 포털"])

_COLLECTION = "quotations"
_PREFIX = "QTN"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("quotation:create"))])
def create_quotation(body: QuotationCreate, user: CurrentUserDep) -> dict[str, Any]:
    """견적서를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    price_list_name: str | None = None
    currency = "KRW"
    if body.price_list_id:
        price_list_doc, items_raw = PriceListService(user.tenant_id).apply_price_list(
            price_list_id=body.price_list_id,
            items=items_raw,
            transaction_date=body.transaction_date,
        )
        price_list_name = str(price_list_doc.get("price_list_name") or "")
        currency = str(price_list_doc.get("currency") or "KRW")
    items_raw, total = calculate_line_totals(items_raw)

    quotation = Quotation(
        _id=doc_id,
        tenant_id=user.tenant_id,
        customer_id=body.customer_id,
        customer_name=body.customer_name,
        transaction_date=body.transaction_date,
        valid_till=body.valid_till,
        price_list_id=body.price_list_id,
        price_list_name=price_list_name,
        currency=currency,
        items=[QuotationItem.model_validate(item) for item in items_raw],
        total=total,
        grand_total=total,
        created_by=user.sub,
        updated_by=user.sub,
    )
    # items에 계산된 amount를 반영
    doc_dict = quotation.model_dump(by_alias=True, exclude_none=True)
    doc_dict["items"] = items_raw
    repo.insert(doc_dict)

    return {"id": doc_id, "message": "견적서가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("quotation:read"))])
def list_quotations(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """견적서 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("quotation:read"))])
def get_quotation(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """견적서 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적서를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("quotation:write"))])
def update_quotation(
    doc_id: str,
    body: QuotationUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """견적서를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적서를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data:
        items_raw = update_data["items"]
        resolved_price_list_id = update_data.get("price_list_id") or doc.get("price_list_id")
        if resolved_price_list_id:
            price_list_doc, items_raw = PriceListService(user.tenant_id).apply_price_list(
                price_list_id=resolved_price_list_id,
                items=items_raw,
                transaction_date=update_data.get("transaction_date") or doc.get("transaction_date"),
            )
            update_data["price_list_name"] = price_list_doc.get("price_list_name")
            update_data["currency"] = price_list_doc.get("currency", "KRW")
        items_raw, total = calculate_line_totals(items_raw)
        update_data["items"] = items_raw
        update_data["total"] = total
        update_data["grand_total"] = total
    elif "price_list_id" in update_data and doc.get("items"):
        price_list_doc, items_raw = PriceListService(user.tenant_id).apply_price_list(
            price_list_id=update_data["price_list_id"],
            items=doc.get("items", []),
            transaction_date=update_data.get("transaction_date") or doc.get("transaction_date"),
        )
        items_raw, total = calculate_line_totals(items_raw)
        update_data["items"] = items_raw
        update_data["total"] = total
        update_data["grand_total"] = total
        update_data["price_list_name"] = price_list_doc.get("price_list_name")
        update_data["currency"] = price_list_doc.get("currency", "KRW")
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "견적서가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("quotation:submit"))])
def submit_quotation(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """견적서를 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적서를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    repo.submit_with_event(
        doc_id,
        event_type=EventType.QUOTATION_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "견적서가 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("quotation:cancel"))])
def cancel_quotation(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """견적서를 취소한다 (제출 → 취소)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적서를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")

    repo.cancel(doc_id)
    return {"id": doc_id, "message": "견적서가 취소되었습니다"}


@router.post("/{quotation_id}/convert", status_code=201)
def convert_quotation(
    quotation_id: str,
    user: CurrentUserDep,
    item_indices: list[int] | None = None,
) -> dict[str, Any]:
    """견적서를 판매주문으로 전환한다."""
    svc = QuotationConversionService(user.tenant_id)
    return svc.convert_to_sales_order(quotation_id, item_indices)


@router.post(
    "/{doc_id}/send-email",
    dependencies=[Depends(require_permission("quotation:write"))],
)
def send_quotation_email(
    doc_id: str,
    body: QuotationSendEmailRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출된 견적서의 PDF와 포털 서명 링크를 메일 발송용으로 준비한다."""
    repo = _get_repo(user.tenant_id)
    svc = QuotationDeliveryService(repo, user.tenant_id)
    return svc.send_email(
        doc_id,
        recipient_email=body.recipient_email,
        subject=body.subject,
        message=body.message,
        actor=user.sub,
    )


@router.get("/{doc_id}/pdf", dependencies=[Depends(require_permission("quotation:read"))])
def download_quotation_pdf(doc_id: str, user: CurrentUserDep) -> Response:
    """견적서 PDF를 내려받는다."""
    repo = _get_repo(user.tenant_id)
    svc = QuotationDeliveryService(repo, user.tenant_id)
    pdf_bytes, file_name = svc.render_pdf(doc_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("quotation:delete"))]
)
def delete_quotation(doc_id: str, user: CurrentUserDep) -> None:
    """견적서를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("견적서를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 삭제할 수 있습니다")

    repo.delete_by_id(doc_id)


@portal_router.post("/{doc_id}/sign")
def portal_sign_quotation(
    doc_id: str,
    body: QuotationPortalSignRequest,
    tenant_id: str | None = Query(default=None),
    tenant_header: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> dict[str, Any]:
    """고객 포털에서 견적서 전자서명을 완료한다."""
    resolved_tenant = tenant_id or tenant_header or get_core_settings().default_tenant
    repo = _get_repo(resolved_tenant)
    svc = QuotationDeliveryService(repo, resolved_tenant)
    return svc.sign_from_portal(
        doc_id,
        token=body.token,
        signer_name=body.signer_name,
        signer_email=body.signer_email,
        signature_text=body.signature_text,
        signature_type=body.signature_type,
    )
