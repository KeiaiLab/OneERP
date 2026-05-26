"""타임시트(Timesheet) CRUD 라우터."""

from __future__ import annotations

from decimal import Decimal
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

from oneerp_projects_app.models.timesheet import Timesheet, TimesheetCreate, TimesheetUpdate
from oneerp_projects_app.services.timesheet_service import TimesheetService

router = APIRouter(prefix="/api/v1/timesheets", tags=["타임시트"])

_COLLECTION = "timesheets"
_PREFIX = "TS"


class TimesheetInvoiceCreate(BaseModel):
    """타임시트 인보이싱 요청 스키마."""

    hourly_rate: Decimal | None = None


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_task_repo(tenant_id: str) -> Repository:
    """작업 실적 누적용 task repository."""
    return Repository("tasks", tenant_id=tenant_id)


def _get_project_billing_repo(tenant_id: str) -> Repository:
    """프로젝트 청구 저장소."""
    return Repository("project_billings", tenant_id=tenant_id)


def _to_public_document(document: dict[str, Any]) -> dict[str, Any]:
    """표준 공개 응답 형태로 변환한다."""
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    return public


def _parse_billed_filter(value: str | None) -> bool | None:
    """문자열 billed 필터를 불리언으로 변환한다."""
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def _decimal_to_float(value: Any) -> Any:
    """API 응답에서 Decimal 값을 JSON 숫자로 노출한다."""
    if isinstance(value, Decimal):
        return float(value)
    return value


def _build_status_badge(document: dict[str, Any], billing_count: int) -> str:
    """타임시트 상태 배지를 계산한다."""
    if document.get("docstatus", 0) == DocStatus.DRAFT:
        return "draft"
    if billing_count > 0 or document.get("billed") is True:
        return "submitted_billed"
    return "submitted_unbilled"


def _build_available_actions(document: dict[str, Any], billing_count: int) -> list[str]:
    """문서 상태에 따른 가능 액션을 계산한다."""
    if document.get("docstatus", 0) == DocStatus.DRAFT:
        return ["submit", "edit", "delete"]
    if billing_count > 0 or document.get("billed") is True:
        return ["view", "view_invoice"]
    return ["create_invoice", "view"]


def _enrich_timesheet(
    document: dict[str, Any],
    *,
    billings: list[dict[str, Any]],
) -> dict[str, Any]:
    """목록/상세 응답에 운영 요약을 주입한다."""
    public = _to_public_document(document)
    total_hours = Decimal(str(document.get("total_hours", 0) or 0))
    billing_total = sum(Decimal(str(billing.get("total", 0) or 0)) for billing in billings)
    billing_ids = [str(billing.get("_id", "")) for billing in billings if billing.get("_id")]
    billing_count = len(billing_ids)
    public["time_log_summary"] = TimesheetService.summarize_time_logs(document)
    public["status_badge"] = _build_status_badge(document, billing_count)
    public["available_actions"] = _build_available_actions(document, billing_count)
    public["billing_summary"] = {
        "billing_count": billing_count,
        "billing_ids": billing_ids,
        "billed": billing_count > 0 or document.get("billed") is True,
        "unbilled": billing_count == 0 and document.get("billed") is not True,
        "total_billed_amount": float(billing_total),
    }
    public["payroll_summary"] = {
        "ready_for_payroll": document.get("docstatus", 0) == DocStatus.SUBMITTED,
        "payroll_ready_hours": float(
            total_hours if document.get("docstatus", 0) == DocStatus.SUBMITTED else Decimal(0)
        ),
    }
    return public


@router.post("", status_code=201, dependencies=[Depends(require_permission("timesheet:create"))])
def create_timesheet(body: TimesheetCreate, user: CurrentUserDep) -> dict[str, Any]:
    """타임시트를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    TimesheetService.validate_draft_document(
        start_date=body.start_date,
        end_date=body.end_date,
        time_logs=[log.model_dump() for log in body.time_logs],
    )

    timesheet = Timesheet(
        _id=doc_id,
        tenant_id=user.tenant_id,
        employee_id=body.employee_id,
        employee_name=body.employee_name,
        start_date=body.start_date,
        end_date=body.end_date,
        total_hours=body.total_hours,
        time_logs=body.time_logs,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(timesheet)
    return {"id": doc_id, "message": "타임시트가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("timesheet:read"))])
def list_timesheets(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    employee_id: str | None = None,
    project_ref: str | None = None,
    docstatus: int | None = None,
    billed: str | None = None,
) -> dict[str, Any]:
    """타임시트 목록을 페이지네이션과 운영 요약으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    docs = repo.find_many(limit=5000, sort=[("created_at", -1)])
    billing_docs = _get_project_billing_repo(user.tenant_id).find_many(
        limit=5000, sort=[("created_at", -1)]
    )
    billing_index: dict[str, list[dict[str, Any]]] = {}
    for billing_doc in billing_docs:
        timesheet_ref = str(billing_doc.get("timesheet_ref", "")).strip()
        if not timesheet_ref:
            continue
        billing_index.setdefault(timesheet_ref, []).append(billing_doc)

    billed_filter = _parse_billed_filter(billed)
    enriched_rows = [
        _enrich_timesheet(document, billings=billing_index.get(str(document.get("_id", "")), []))
        for document in docs
    ]
    filtered_rows: list[dict[str, Any]] = []
    for row in enriched_rows:
        if employee_id and row.get("employee_id", "") != employee_id:
            continue
        if project_ref and project_ref not in row["time_log_summary"]["project_refs"]:
            continue
        if docstatus is not None and int(row.get("docstatus", 0)) != docstatus:
            continue
        if billed_filter is not None and row["billing_summary"]["billed"] is not billed_filter:
            continue
        filtered_rows.append(row)

    total_count = len(filtered_rows)
    skip = (page - 1) * page_size
    page_rows = filtered_rows[skip : skip + page_size]
    submitted_rows = [
        row for row in filtered_rows if int(row.get("docstatus", 0)) == DocStatus.SUBMITTED
    ]
    draft_rows = [row for row in filtered_rows if int(row.get("docstatus", 0)) == DocStatus.DRAFT]
    return {
        "data": page_rows,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "summary": {
            "draft_count": len(draft_rows),
            "submitted_count": len(submitted_rows),
            "billed_count": sum(1 for row in filtered_rows if row["billing_summary"]["billed"]),
            "unbilled_count": sum(1 for row in filtered_rows if row["billing_summary"]["unbilled"]),
            "payroll_ready_hours": round(
                sum(row["payroll_summary"]["payroll_ready_hours"] for row in filtered_rows),
                2,
            ),
            "unbilled_hours": round(
                sum(
                    float(row.get("total_hours", 0) or 0)
                    for row in filtered_rows
                    if row["billing_summary"]["unbilled"]
                ),
                2,
            ),
        },
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("timesheet:read"))])
def get_timesheet(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """타임시트 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("타임시트를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    billings = _get_project_billing_repo(user.tenant_id).find_many(
        query={"timesheet_ref": doc_id},
        limit=100,
        sort=[("created_at", -1)],
    )
    return _enrich_timesheet(doc, billings=billings)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("timesheet:write"))])
def update_timesheet(
    doc_id: str,
    body: TimesheetUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """타임시트를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("타임시트를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise_bad_request("수정할 내용이 없습니다")
    TimesheetService.validate_draft_document(
        start_date=update_data.get("start_date", doc.get("start_date")),
        end_date=update_data.get("end_date", doc.get("end_date")),
        time_logs=update_data.get("time_logs", doc.get("time_logs", []) or []),
    )
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "타임시트가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("timesheet:submit"))])
def submit_timesheet(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """타임시트를 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("타임시트를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    total_hours, time_logs = TimesheetService.validate_submission_document(doc)
    if time_logs:
        TimesheetService.apply_task_actual_time_rollup(_get_task_repo(user.tenant_id), time_logs)
    event_data = TimesheetService.build_submission_event_data(doc, total_hours)
    repo.submit_with_event(
        doc_id,
        event_type=EventType.TIMESHEET_SUBMITTED,
        event_data=event_data,
        triggered_by=user.sub,
    )
    return {
        "id": doc_id,
        "message": "타임시트가 제출되었습니다",
        "status": "submitted",
        "total_hours": total_hours,
    }


@router.post(
    "/{doc_id}/invoice",
    dependencies=[Depends(require_permission("project_billing:create"))],
)
def invoice_timesheet(
    doc_id: str,
    body: TimesheetInvoiceCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출 완료 타임시트에서 청구 초안을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("타임시트를 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출 완료된 타임시트만 청구할 수 있습니다")
    if doc.get("billed") is True:
        raise_bad_request("이미 청구된 타임시트입니다")

    service = TimesheetService(user.tenant_id)
    result = service.generate_invoice_from_timesheet(
        doc_id,
        hourly_rate=body.hourly_rate,
    )
    return {key: _decimal_to_float(value) for key, value in result.items()}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("timesheet:delete"))]
)
def delete_timesheet(doc_id: str, user: CurrentUserDep) -> None:
    """타임시트를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("타임시트를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    try:
        repo.delete_by_id(doc_id)
    except ValueError as exc:
        raise_bad_request(str(exc))
