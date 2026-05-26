"""마일스톤(Milestone) 워크벤치 라우트."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.milestone import Milestone, MilestoneCreate, MilestoneUpdate

router = APIRouter(prefix="/api/v1/milestones", tags=["마일스톤"])
_COLLECTION = "milestones"
_PREFIX = "MLS"


def _get_repo(tenant_id: str) -> Repository:
    """현재 tenant에 바인딩된 마일스톤 저장소를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_billing_repo(tenant_id: str) -> Repository:
    """현재 tenant에 바인딩된 프로젝트 청구 저장소를 반환한다."""
    return Repository("project_billings", tenant_id=tenant_id)


def _to_public_document(document: dict[str, Any]) -> dict[str, Any]:
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    return public


def _coerce_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _resolve_status(document: dict[str, Any], *, as_of_date: date) -> str:
    status = str(document.get("status", "pending") or "pending")
    if status == "completed":
        return "completed"
    due_date = _coerce_date(document.get("due_date"))
    if due_date and due_date < as_of_date:
        return "overdue"
    return "pending"


def _pick_billing(
    document: dict[str, Any], billings: list[dict[str, Any]]
) -> dict[str, Any] | None:
    billing_id = str(document.get("billing_id", "")).strip()
    if billing_id:
        for billing in billings:
            if str(billing.get("_id", "")) == billing_id:
                return billing
    return billings[0] if billings else None


def _build_billing_summary(
    document: dict[str, Any], billings: list[dict[str, Any]]
) -> dict[str, Any]:
    billing_required = Decimal(str(document.get("billing_amount", 0) or 0)) > 0
    billing = _pick_billing(document, billings)
    billing_id = ""
    billing_status = "not_required"
    is_invoiced = False
    if billing_required:
        if billing:
            billing_id = str(billing.get("_id", ""))
            is_invoiced = bool(billing.get("is_invoiced"))
            billing_status = "invoiced" if is_invoiced else "ready_to_invoice"
        else:
            billing_status = "pending_generation"
    return {
        "billing_required": billing_required,
        "billing_id": billing_id,
        "billing_status": billing_status,
        "billing_amount": float(Decimal(str(document.get("billing_amount", 0) or 0))),
        "is_invoiced": is_invoiced,
    }


def _build_status_badge(status: str, billing_summary: dict[str, Any]) -> str:
    if status == "overdue":
        return "overdue"
    if status == "completed":
        if billing_summary["billing_status"] == "invoiced":
            return "completed_billed"
        if billing_summary["billing_status"] == "ready_to_invoice":
            return "completed_ready_to_invoice"
        return "completed"
    return "pending"


def _build_available_actions(status: str, billing_summary: dict[str, Any]) -> list[str]:
    if status == "completed":
        if billing_summary["billing_status"] in {"ready_to_invoice", "invoiced"}:
            return ["view", "open_billing"]
        return ["view"]
    return ["edit", "complete", "delete"]


def _serialize_milestone(
    document: dict[str, Any],
    *,
    as_of_date: date,
    billings: list[dict[str, Any]],
) -> dict[str, Any]:
    public = _to_public_document(document)
    resolved_status = _resolve_status(document, as_of_date=as_of_date)
    billing_summary = _build_billing_summary(document, billings)
    public["status"] = resolved_status
    public["status_badge"] = _build_status_badge(resolved_status, billing_summary)
    public["billing_summary"] = billing_summary
    public["available_actions"] = _build_available_actions(resolved_status, billing_summary)
    return public


def _summarize(documents: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "pending": 0,
        "completed": 0,
        "overdue": 0,
        "ready_to_invoice_count": 0,
        "invoiced_count": 0,
        "total_billing_amount": 0.0,
    }
    for document in documents:
        status = str(document.get("status", "pending") or "pending")
        if status in summary:
            summary[status] += 1
        billing_summary = document.get("billing_summary", {})
        if billing_summary.get("billing_status") == "ready_to_invoice":
            summary["ready_to_invoice_count"] += 1
        if billing_summary.get("billing_status") == "invoiced":
            summary["invoiced_count"] += 1
        summary["total_billing_amount"] += float(billing_summary.get("billing_amount", 0.0) or 0.0)
    summary["total"] = len(documents)
    summary["total_billing_amount"] = round(summary["total_billing_amount"], 2)
    return summary


@router.post("/", status_code=201, dependencies=[Depends(require_permission("milestone:create"))])
async def create_milestone(body: MilestoneCreate, user: CurrentUserDep) -> dict[str, Any]:
    """마일스톤을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    milestone = Milestone(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **body.model_dump(),
    )
    repo.insert(milestone)
    return {"milestone_id": doc_id, "message": "마일스톤이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("milestone:read"))])
async def list_milestones(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    project: str | None = None,
    status: str | None = None,
    billing_status: str | None = None,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    """마일스톤 목록을 페이지네이션과 청구 워크벤치 요약으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if project:
        query["project"] = project
    effective_date = as_of_date or datetime.now(tz=UTC).date()
    raw_docs = repo.find_many(query, skip=0, limit=5000, sort=[("due_date", 1), ("created_at", -1)])
    billing_docs = _get_billing_repo(user.tenant_id).find_many(
        limit=5000, sort=[("created_at", -1)]
    )
    billing_index: dict[str, list[dict[str, Any]]] = {}
    for billing_doc in billing_docs:
        milestone_id = str(billing_doc.get("milestone_id", "")).strip()
        if not milestone_id:
            continue
        billing_index.setdefault(milestone_id, []).append(billing_doc)

    rows = [
        _serialize_milestone(
            document,
            as_of_date=effective_date,
            billings=billing_index.get(str(document.get("_id", "")), []),
        )
        for document in raw_docs
    ]
    if status:
        rows = [row for row in rows if row["status"] == status]
    if billing_status:
        rows = [row for row in rows if row["billing_summary"]["billing_status"] == billing_status]
    total = len(rows)
    skip = (page - 1) * page_size
    data = rows[skip : skip + page_size]
    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _summarize(rows),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("milestone:read"))])
async def get_milestone(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """마일스톤 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found("마일스톤을 찾을 수 없습니다")
    document = cast("dict[str, Any]", document)
    billings = _get_billing_repo(user.tenant_id).find_many({"milestone_id": doc_id}, limit=100)
    return _serialize_milestone(document, as_of_date=datetime.now(tz=UTC).date(), billings=billings)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("milestone:write"))])
async def update_milestone(
    doc_id: str, body: MilestoneUpdate, user: CurrentUserDep
) -> dict[str, Any]:
    """마일스톤을 수정한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found("마일스톤을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise_bad_request("수정할 내용이 없습니다")
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"message": "마일스톤이 수정되었습니다"}


@router.post(
    "/{doc_id}/complete",
    dependencies=[Depends(require_permission("milestone:write"))],
)
async def complete_milestone(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """마일스톤을 완료 처리하고 필요 시 마일스톤 기반 청구 초안을 생성한다."""
    repo = _get_repo(user.tenant_id)
    billing_repo = _get_billing_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found("마일스톤을 찾을 수 없습니다")
    document = cast("dict[str, Any]", document)

    billing_amount = Decimal(str(document.get("billing_amount", 0) or 0))
    project_id = str(document.get("project", "")).strip()
    billing_id = str(document.get("billing_id", "")).strip()
    if billing_amount > 0 and not project_id:
        raise_bad_request("프로젝트가 연결된 마일스톤만 청구를 생성할 수 있습니다")

    if billing_amount > 0 and not billing_id:
        billing_id = generate_name("PBL", tenant_id=user.tenant_id)
        billing_repo.insert(
            {
                "_id": billing_id,
                "tenant_id": user.tenant_id,
                "project_id": project_id,
                "project": project_id,
                "billing_date": datetime.now(tz=UTC).date(),
                "billing_type": "Milestone",
                "amount": billing_amount,
                "total": billing_amount,
                "status": "draft",
                "is_invoiced": False,
                "milestone_id": doc_id,
                "milestone_name": document.get("milestone_name", ""),
            }
        )

    completed_at = datetime.now(tz=UTC)
    update_data: dict[str, Any] = {
        "status": "completed",
        "completed_at": completed_at,
        "updated_by": user.sub,
    }
    if billing_id:
        update_data["billing_id"] = billing_id
    repo.update_by_id(doc_id, update_data)
    return {
        "milestone_id": doc_id,
        "status": "completed",
        "completed_at": completed_at,
        "billing_id": billing_id,
    }


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("milestone:delete"))])
async def delete_milestone(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """청구가 연결되지 않은 마일스톤만 삭제한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found("마일스톤을 찾을 수 없습니다")
    document = cast("dict[str, Any]", document)
    if document.get("billing_id"):
        raise_bad_request("청구가 연결된 마일스톤은 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "마일스톤이 삭제되었습니다"}
