"""기회(Opportunity) API 라우터."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 요청 바디 검증 런타임 필요
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel

from oneerp_crm_app.models.opportunity import Opportunity, OpportunityCreate, OpportunityUpdate
from oneerp_crm_app.services.pipeline_service import PipelineService


class AdvanceStageBody(BaseModel):
    """단계 진행 요청 스키마."""

    stage: str


class ConvertToQuotationBody(BaseModel):
    """견적 전환 요청 스키마."""

    customer_id: str
    items: list[dict[str, Any]]
    valid_till: date | None = None


class MarkLostBody(BaseModel):
    """실패 처리 요청 스키마."""

    lost_reason: str = ""
    competitor: str = ""


router = APIRouter(prefix="/api/v1/opportunities", tags=["기회"])

_COLLECTION = "opportunities"
_PREFIX = "OPP"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("opportunity:create"))])
def create_opportunity(body: OpportunityCreate, user: CurrentUserDep) -> dict[str, Any]:
    """기회를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    opportunity = Opportunity(
        _id=doc_id,
        tenant_id=user.tenant_id,
        lead_ref=body.lead_ref,
        customer_id=body.customer_id,
        opportunity_type=body.opportunity_type,
        expected_amount=body.expected_amount,
        probability=body.probability,
        close_date=body.close_date,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(opportunity)
    return {"id": doc_id, "message": "기회가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("opportunity:read"))])
def list_opportunities(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """기회 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("opportunity:read"))])
def get_opportunity(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """기회 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("기회를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("opportunity:write"))])
def update_opportunity(
    doc_id: str,
    body: OpportunityUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """기회를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("기회를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "기회가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("opportunity:submit"))])
def submit_opportunity(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """기회를 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("기회를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    repo.submit_with_event(
        doc_id, event_type=EventType.OPPORTUNITY_SUBMITTED, triggered_by=user.sub
    )
    return {"id": doc_id, "message": "기회가 제출되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("opportunity:delete"))]
)
def delete_opportunity(doc_id: str, user: CurrentUserDep) -> None:
    """기회를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("기회를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    repo.delete_by_id(doc_id)


@router.post(
    "/{doc_id}/advance-stage",
    dependencies=[Depends(require_permission("opportunity:write"))],
)
def advance_opportunity_stage(
    doc_id: str, body: AdvanceStageBody, user: CurrentUserDep
) -> dict[str, Any]:
    """기회의 단계를 진행한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    try:
        return service.advance_stage(doc_id, body.stage)
    except ValueError as e:
        raise_bad_request(str(e))


@router.post(
    "/{doc_id}/convert-to-quotation",
    dependencies=[Depends(require_permission("opportunity:write"))],
)
def convert_to_quotation(
    doc_id: str, body: ConvertToQuotationBody, user: CurrentUserDep
) -> dict[str, Any]:
    """기회를 견적으로 전환한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    try:
        return service.convert_opportunity_to_quotation(
            doc_id, body.customer_id, body.items, body.valid_till
        )
    except ValueError as e:
        raise_bad_request(str(e))


@router.post(
    "/{doc_id}/won",
    dependencies=[Depends(require_permission("opportunity:write"))],
)
def mark_opportunity_won(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """기회를 성사(won)로 표시한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    try:
        return service.mark_won(doc_id)
    except ValueError as e:
        raise_bad_request(str(e))


@router.post(
    "/{doc_id}/lost",
    dependencies=[Depends(require_permission("opportunity:write"))],
)
def mark_opportunity_lost(doc_id: str, body: MarkLostBody, user: CurrentUserDep) -> dict[str, Any]:
    """기회를 실패(lost)로 표시한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    try:
        return service.mark_lost(doc_id, body.lost_reason, body.competitor)
    except ValueError as e:
        raise_bad_request(str(e))
