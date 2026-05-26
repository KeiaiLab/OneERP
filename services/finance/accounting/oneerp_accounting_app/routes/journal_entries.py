"""분개전표 CRUD 라우터 — 차대변 일치 검증, 마감 기간 검증 포함.

L2 API 계약:
- POST /api/v1/journal-entries — 분개전표 생성 (BR-ACCT-001/002/003)
- GET /api/v1/journal-entries — 분개전표 목록
- GET /api/v1/journal-entries/{doc_id} — 분개전표 조회
- PUT /api/v1/journal-entries/{doc_id} — 분개전표 수정 (BR-ACCT-004)
- POST /api/v1/journal-entries/{doc_id}/submit — 분개전표 제출
- POST /api/v1/journal-entries/{doc_id}/cancel — 분개전표 취소
- DELETE /api/v1/journal-entries/{doc_id} — 초안 분개전표 삭제
"""

from __future__ import annotations

from calendar import monthrange
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.audit import AuditEvent, emit_audit_event
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_unprocessable
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.route_helpers import (
    cancel_document,
    check_draft_status,
    get_or_404,
    paginated_list,
    submit_document,
)
from pydantic import BaseModel

from ..dto import JournalEntryCreate, JournalEntryUpdate
from ..models.journal_entry import (
    JournalEntry,
    JournalEntryApprovalRequest,
    JournalEntryRejectRequest,
    JournalEntryTemplate,
    JournalEntryTemplateCreate,
    JournalEntryTemplateInstantiate,
)
from ..services.journal_auto_service import JournalAutoService
from ..services.journal_entry_service import (
    get_accounting_period_repo,
    get_journal_entry_repo,
    get_template_repo,
)

router = APIRouter(prefix="/api/v1/journal-entries", tags=["분개전표"])

_COLLECTION = "journal_entries"
_PREFIX = "JE"
_NOT_FOUND = "분개전표를 찾을 수 없습니다"
_TEMPLATE_COLLECTION = "journal_entry_templates"
_TEMPLATE_PREFIX = "JETPL"
_TEMPLATE_NOT_FOUND = "반복 전표 템플릿을 찾을 수 없습니다"


def _get_repo(tenant_id: str):
    """분개전표 Repository를 서비스 레이어를 통해 획득한다 (OE002)."""
    return get_journal_entry_repo(tenant_id)


def _get_template_repo(tenant_id: str):
    """반복 전표 템플릿 Repository를 서비스 레이어를 통해 획득한다 (OE002)."""
    return get_template_repo(tenant_id)


class _LedgerApplyRequest(BaseModel):
    journal_entry_id: str
    tenant_id: str
    total_debit: str | float | int = "0"
    total_credit: str | float | int = "0"


class _PayrollJournalCreateRequest(BaseModel):
    payroll_entry_id: str
    tenant_id: str
    employee_count: int = 0
    total_amount: float = 0
    posting_date: str | None = None


def _check_period_open(tenant_id: str, posting_date: Any) -> None:
    """BR-ACCT-003: 마감된 회계기간에 전기할 수 없다."""
    if posting_date is None:
        return
    period_repo = get_accounting_period_repo(tenant_id)
    periods = period_repo.find_many(
        {
            "start_date": {"$lte": posting_date},
            "end_date": {"$gte": posting_date},
        },
        limit=1,
    )
    if periods and periods[0].get("status") == "closed":
        raise_unprocessable(
            "ERR-ACCT-031",
            f"마감된 회계기간에는 전표를 입력할 수 없습니다 (전기일: {posting_date})",
        )


def _calculate_totals(items: list[Any]) -> tuple[Decimal, Decimal]:
    """라인 아이템 합계를 계산한다."""
    total_debit = sum(
        (
            Decimal(str(item.debit if hasattr(item, "debit") else item.get("debit", 0)))
            for item in items
        ),
        Decimal(0),
    )
    total_credit = sum(
        (
            Decimal(str(item.credit if hasattr(item, "credit") else item.get("credit", 0)))
            for item in items
        ),
        Decimal(0),
    )
    return total_debit, total_credit


def _assert_editable_draft(doc: dict[str, Any], action_name: str) -> None:
    """승인 대기 중이 아닌 초안 문서만 수정/삭제할 수 있다."""
    check_draft_status(doc, action_name)
    if doc.get("approval_status") == "pending":
        raise_bad_request(f"승인 대기 중인 전표는 {action_name}할 수 없습니다")


def _assert_pending_approval(doc: dict[str, Any], user: CurrentUserDep) -> None:
    """승인/반려 가능 상태와 결재자 권한을 검증한다."""
    if int(doc.get("docstatus", 0)) != int(DocStatus.DRAFT):
        raise_bad_request("초안 상태의 승인 대기 전표만 처리할 수 있습니다")
    if doc.get("approval_status") != "pending":
        raise_bad_request("승인 대기 상태의 전표만 처리할 수 있습니다")
    required_approver = str(doc.get("required_approver", "")).strip()
    if required_approver and required_approver != user.sub:
        raise_unprocessable(
            "ERR-ACCT-032", "지정된 결재자만 이 전표를 승인 또는 반려할 수 있습니다"
        )


def _add_months(value: date, months: int) -> date:
    """월 단위 반복 일자를 계산한다."""
    raw_month = value.month - 1 + months
    year = value.year + raw_month // 12
    month = raw_month % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def _advance_next_posting_date(current: date, recurrence_unit: str, interval: int) -> date:
    """다음 반복 전기일을 계산한다."""
    if recurrence_unit == "daily":
        return current.fromordinal(current.toordinal() + interval)
    if recurrence_unit == "weekly":
        return current.fromordinal(current.toordinal() + (interval * 7))
    if recurrence_unit == "quarterly":
        return _add_months(current, interval * 3)
    if recurrence_unit == "yearly":
        return _add_months(current, interval * 12)
    return _add_months(current, interval)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("journal_entry:create"))]
)
def create_journal_entry(body: JournalEntryCreate, user: CurrentUserDep) -> dict[str, Any]:
    """분개전표를 생성한다.

    에러 응답 (L3 에러 카탈로그):
    - 400 ERR-ACCT-001: 필수값 누락
    - 403 ERR-ACCT-010: 권한 부족
    - 422 ERR-ACCT-030: 차대변 불일치 (BR-ACCT-001)
    - 422 ERR-ACCT-031: 마감 기간 전기 (BR-ACCT-003)
    """
    # BR-ACCT-003: 마감 기간 검증
    _check_period_open(user.tenant_id, body.posting_date)

    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    total_debit, total_credit = _calculate_totals(body.items)

    entry = JournalEntry(
        _id=doc_id,
        tenant_id=user.tenant_id,
        posting_date=body.posting_date,
        voucher_type=body.voucher_type,
        total_debit=total_debit,
        total_credit=total_credit,
        items=[item.model_dump() for item in body.items],
        remark=body.remark,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(entry)
    # G3-4 감사: GL 변경은 모두 audit_events 에 기록. 차대 합계와 전기일자가 핵심 증거.
    emit_audit_event(
        AuditEvent(
            actor=user.sub,
            action="journal_entry.create",
            resource=f"journal_entries/{doc_id}",
            tenant_id=user.tenant_id,
            details={
                "voucher_type": body.voucher_type,
                "posting_date": body.posting_date.isoformat(),
                "total_debit": str(total_debit),
                "total_credit": str(total_credit),
                "item_count": len(body.items),
            },
        ),
    )
    return {
        "_id": doc_id,
        **body.model_dump(mode="json"),
        "total_debit": total_debit,
        "total_credit": total_credit,
    }


@router.get("", dependencies=[Depends(require_permission("journal_entry:read"))])
def list_journal_entries(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    voucher_no: str | None = None,
) -> dict[str, Any]:
    """분개전표 목록을 페이지네이션으로 조회한다.

    필터:
        voucher_no: 원본 전표 번호 (경비청구 ID, 급여대장 ID 등)
    """
    repo = _get_repo(user.tenant_id)
    filter_query: dict[str, Any] = {}
    if voucher_no:
        filter_query["voucher_no"] = voucher_no
    return paginated_list(repo, page, page_size, filter_query=filter_query)


@router.post(
    "/templates",
    status_code=201,
    dependencies=[Depends(require_permission("journal_entry:create"))],
)
def create_journal_entry_template(
    body: JournalEntryTemplateCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """반복 전표 템플릿을 생성한다."""
    repo = _get_template_repo(user.tenant_id)
    template_id = generate_name(_TEMPLATE_PREFIX, tenant_id=user.tenant_id)
    template = JournalEntryTemplate(
        _id=template_id,
        tenant_id=user.tenant_id,
        template_name=body.template_name,
        description=body.description,
        voucher_type=body.voucher_type,
        recurrence_unit=body.recurrence_unit,
        interval=body.interval,
        next_posting_date=body.next_posting_date,
        items=body.items,
        remark=body.remark,
        default_approver=body.default_approver,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(template)
    return {
        "_id": template_id,
        **body.model_dump(mode="json"),
        "usage_count": 0,
    }


@router.get("/templates", dependencies=[Depends(require_permission("journal_entry:read"))])
def list_journal_entry_templates(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """반복 전표 템플릿 목록을 조회한다."""
    return paginated_list(_get_template_repo(user.tenant_id), page, page_size)


@router.get(
    "/templates/{template_id}",
    dependencies=[Depends(require_permission("journal_entry:read"))],
)
def get_journal_entry_template(template_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """반복 전표 템플릿 상세를 조회한다."""
    return get_or_404(_get_template_repo(user.tenant_id), template_id, _TEMPLATE_NOT_FOUND)


@router.post(
    "/templates/{template_id}/instantiate",
    status_code=201,
    dependencies=[Depends(require_permission("journal_entry:create"))],
)
def instantiate_journal_entry_template(
    template_id: str,
    body: JournalEntryTemplateInstantiate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """반복 전표 템플릿으로 새 분개 초안을 생성한다."""
    _check_period_open(user.tenant_id, body.posting_date)
    template_repo = _get_template_repo(user.tenant_id)
    template = get_or_404(template_repo, template_id, _TEMPLATE_NOT_FOUND)

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    items = list(template.get("items", []))
    total_debit, total_credit = _calculate_totals(items)
    required_approver = body.required_approver or template.get("default_approver", "")
    approval_required = bool(required_approver)
    entry = JournalEntry(
        _id=doc_id,
        tenant_id=user.tenant_id,
        posting_date=body.posting_date,
        voucher_type=template.get("voucher_type", "journal_entry"),
        total_debit=total_debit,
        total_credit=total_credit,
        items=items,
        remark=body.remark if body.remark is not None else template.get("remark", ""),
        template_id=template_id,
        approval_required=approval_required,
        approval_status="not_requested",
        required_approver=required_approver,
        created_by=user.sub,
        updated_by=user.sub,
    )
    _get_repo(user.tenant_id).insert(entry)

    template_update: dict[str, Any] = {
        "usage_count": int(template.get("usage_count", 0) or 0) + 1,
        "updated_by": user.sub,
    }
    if template.get("next_posting_date"):
        template_update["next_posting_date"] = _advance_next_posting_date(
            body.posting_date,
            str(template.get("recurrence_unit", "monthly")),
            int(template.get("interval", 1) or 1),
        )
    template_repo.update_by_id(template_id, template_update)

    return {
        "_id": doc_id,
        "template_id": template_id,
        "posting_date": body.posting_date.isoformat(),
        "voucher_type": template.get("voucher_type", "journal_entry"),
        "total_debit": total_debit,
        "total_credit": total_credit,
        "required_approver": required_approver,
        "approval_required": approval_required,
    }


@router.post("/from-payroll-entry", status_code=201)
def create_journal_entry_from_payroll(body: _PayrollJournalCreateRequest) -> dict[str, Any]:
    """급여 이벤트 payload를 단순 급여 분개전표로 변환한다."""
    service = JournalAutoService(body.tenant_id)
    journal_entry_id = service.create_payroll_journal_from_event(
        {
            "doc_id": body.payroll_entry_id,
            "employee_count": body.employee_count,
            "posting_date": body.posting_date or "",
            "total_gross": body.total_amount,
            "total_net": body.total_amount,
            "total_employee_insurance": 0,
            "total_employer_insurance": 0,
            "total_income_tax": 0,
            "total_local_income_tax": 0,
        }
    )
    return {
        "id": journal_entry_id,
        "payroll_entry_id": body.payroll_entry_id,
        "message": "급여대장 기준 분개전표가 생성되었습니다",
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("journal_entry:read"))])
def get_journal_entry(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """분개전표를 조회한다."""
    repo = _get_repo(user.tenant_id)
    return get_or_404(repo, doc_id, _NOT_FOUND)


@router.post("/{doc_id}/apply-to-ledger")
def apply_journal_entry_to_ledger(doc_id: str, body: _LedgerApplyRequest) -> dict[str, Any]:
    """내부 원장 반영 완료 상태를 기록한다."""
    repo = _get_repo(body.tenant_id)
    get_or_404(repo, doc_id, _NOT_FOUND)
    repo.update_by_id(
        doc_id,
        {
            "ledger_applied": True,
            "ledger_applied_at": datetime.now(tz=UTC),
            "ledger_total_debit": str(body.total_debit),
            "ledger_total_credit": str(body.total_credit),
        },
    )
    return {
        "id": doc_id,
        "message": "분개전표 원장 반영이 기록되었습니다",
    }


@router.put("/{doc_id}", dependencies=[Depends(require_permission("journal_entry:write"))])
def update_journal_entry(
    doc_id: str, body: JournalEntryUpdate, user: CurrentUserDep
) -> dict[str, Any]:
    """분개전표를 수정한다.

    BR-ACCT-004: Draft 상태에서만 수정 가능.
    BR-ACCT-003: 변경된 posting_date가 마감 기간이면 거부.
    """
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "수정")
    if doc.get("approval_status") == "pending":
        raise_bad_request("승인 대기 중인 전표는 수정할 수 없습니다")

    # BR-ACCT-003: posting_date 변경 시 마감 기간 검증
    if body.posting_date is not None:
        _check_period_open(user.tenant_id, body.posting_date)

    update_data = body.model_dump(exclude_none=True, mode="json")
    update_data["updated_by"] = user.sub

    # items가 변경된 경우 합계를 재계산한다
    if body.items is not None:
        update_data["total_debit"] = float(sum(item.debit for item in body.items))
        update_data["total_credit"] = float(sum(item.credit for item in body.items))
        update_data["items"] = [item.model_dump(mode="json") for item in body.items]

    repo.update_by_id(doc_id, update_data)
    return {**doc, **update_data}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("journal_entry:submit"))])
def submit_journal_entry(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """분개전표를 제출 상태로 변경한다 (draft → submitted).

    이벤트 발행: JOURNAL_ENTRY_SUBMITTED
    """
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)

    # BR-ACCT-003: 제출 시에도 마감 기간 검증
    _check_period_open(user.tenant_id, doc.get("posting_date"))

    submit_document(repo, doc_id, _NOT_FOUND)
    if doc.get("approval_required"):
        approval_status = str(doc.get("approval_status", "not_requested"))
        if approval_status == "pending":
            raise_bad_request("승인 대기 중인 전표는 승인 완료 후 제출할 수 있습니다")
        if approval_status == "rejected":
            raise_bad_request("반려된 전표는 수정 후 다시 승인 요청해야 합니다")

    repo.update_with_event(
        doc_id,
        update={
            "docstatus": DocStatus.SUBMITTED,
            "approval_status": "not_required" if not doc.get("approval_required") else "approved",
            "approved_by": user.sub if doc.get("approval_required") else "",
            "approved_at": datetime.now(tz=UTC) if doc.get("approval_required") else None,
        },
        event_type=EventType.JOURNAL_ENTRY_SUBMITTED,
        event_data={
            "voucher_type": doc.get("voucher_type", ""),
            "total_debit": str(doc.get("total_debit", 0)),
            "total_credit": str(doc.get("total_credit", 0)),
        },
        triggered_by=user.sub,
    )

    return {"id": doc_id, "message": "분개전표가 제출되었습니다"}


@router.post(
    "/{doc_id}/request-approval",
    dependencies=[Depends(require_permission("journal_entry:submit"))],
)
def request_journal_entry_approval(
    doc_id: str,
    body: JournalEntryApprovalRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """분개전표 승인 요청을 등록한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    _assert_editable_draft(doc, "승인 요청")
    repo.update_by_id(
        doc_id,
        {
            "approval_required": True,
            "approval_status": "pending",
            "required_approver": body.approver,
            "approval_requested_by": user.sub,
            "approval_requested_at": datetime.now(tz=UTC),
            "approval_comment": body.comment,
            "approved_by": "",
            "approved_at": None,
            "rejected_by": "",
            "rejected_at": None,
            "rejection_reason": "",
            "updated_by": user.sub,
        },
    )
    return {
        "id": doc_id,
        "approval_status": "pending",
        "required_approver": body.approver,
        "message": "분개전표 승인 요청이 등록되었습니다",
    }


@router.post(
    "/{doc_id}/approve",
    dependencies=[Depends(require_permission("journal_entry:approve"))],
)
def approve_journal_entry(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """승인 대기 중인 분개전표를 승인하고 제출 처리한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    _assert_pending_approval(doc, user)
    _check_period_open(user.tenant_id, doc.get("posting_date"))
    repo.update_with_event(
        doc_id,
        update={
            "docstatus": DocStatus.SUBMITTED,
            "approval_status": "approved",
            "approved_by": user.sub,
            "approved_at": datetime.now(tz=UTC),
            "rejected_by": "",
            "rejected_at": None,
            "rejection_reason": "",
            "updated_by": user.sub,
        },
        event_type=EventType.JOURNAL_ENTRY_SUBMITTED,
        event_data={
            "voucher_type": doc.get("voucher_type", ""),
            "total_debit": str(doc.get("total_debit", 0)),
            "total_credit": str(doc.get("total_credit", 0)),
            "approved_by": user.sub,
        },
        triggered_by=user.sub,
    )
    return {
        "id": doc_id,
        "approval_status": "approved",
        "message": "분개전표가 승인되어 제출되었습니다",
    }


@router.post(
    "/{doc_id}/reject",
    dependencies=[Depends(require_permission("journal_entry:reject"))],
)
def reject_journal_entry(
    doc_id: str,
    body: JournalEntryRejectRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """승인 대기 중인 분개전표를 반려한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    _assert_pending_approval(doc, user)
    repo.update_by_id(
        doc_id,
        {
            "approval_status": "rejected",
            "rejected_by": user.sub,
            "rejected_at": datetime.now(tz=UTC),
            "rejection_reason": body.reason,
            "updated_by": user.sub,
        },
    )
    return {
        "id": doc_id,
        "approval_status": "rejected",
        "message": "분개전표가 반려되었습니다",
    }


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("journal_entry:cancel"))])
def cancel_journal_entry(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """분개전표를 취소 상태로 변경한다 (submitted → cancelled).

    이벤트 발행: JOURNAL_ENTRY_CANCELLED
    """
    repo = _get_repo(user.tenant_id)
    cancel_document(repo, doc_id, _NOT_FOUND)
    repo.update_with_event(
        doc_id,
        update={},
        event_type=EventType.JOURNAL_ENTRY_CANCELLED,
        triggered_by=user.sub,
    )

    return {"id": doc_id, "message": "분개전표가 취소되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("journal_entry:delete"))],
)
def delete_journal_entry(doc_id: str, user: CurrentUserDep) -> None:
    """분개전표를 삭제한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    _assert_editable_draft(doc, "삭제")
    repo.delete_by_id(doc_id)
