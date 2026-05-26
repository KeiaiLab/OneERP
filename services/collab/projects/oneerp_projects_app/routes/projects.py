"""프로젝트(Project) CRUD 라우터."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_projects_app.models.project import Project, ProjectCreate, ProjectUpdate
from oneerp_projects_app.models.task import Task

router = APIRouter(prefix="/api/v1/projects", tags=["프로젝트"])

_COLLECTION = "projects"
_PREFIX = "PROJ"
_TASK_PREFIX = "TASK"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_project_template_repo(tenant_id: str) -> Repository:
    """프로젝트 템플릿 저장소를 반환한다."""
    return Repository("project_templates", tenant_id=tenant_id)


def _get_task_repo(tenant_id: str) -> Repository:
    """태스크 저장소를 반환한다."""
    return Repository("tasks", tenant_id=tenant_id)


def _get_employee_repo(tenant_id: str) -> Repository:
    """직원 저장소를 반환한다."""
    return Repository("employees", tenant_id=tenant_id)


def _get_milestone_repo(tenant_id: str) -> Repository:
    """마일스톤 저장소를 반환한다."""
    return Repository("milestones", tenant_id=tenant_id)


def _get_resource_allocation_repo(tenant_id: str) -> Repository:
    """자원 배정 저장소를 반환한다."""
    return Repository("resource_allocations", tenant_id=tenant_id)


def _get_project_billing_repo(tenant_id: str) -> Repository:
    """프로젝트 청구 저장소를 반환한다."""
    return Repository("project_billings", tenant_id=tenant_id)


def _get_timesheet_repo(tenant_id: str) -> Repository:
    """타임시트 저장소를 반환한다."""
    return Repository("timesheets", tenant_id=tenant_id)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    """공개 응답용 id 필드를 추가한다."""
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    return public


def _resolve_template_tasks(tenant_id: str, template_id: str) -> list[str]:
    """프로젝트 템플릿의 기본 태스크 목록을 반환한다."""
    if not template_id:
        return []
    template = _get_project_template_repo(tenant_id).find_by_id(template_id)
    if not template:
        raise_not_found("프로젝트 템플릿을 찾을 수 없습니다")
    template = cast("dict[str, Any]", template)
    return [task.strip() for task in template.get("default_tasks", []) if task.strip()]


def _create_template_tasks(
    tenant_id: str,
    *,
    project_id: str,
    task_subjects: list[str],
    created_by: str,
) -> list[str]:
    """프로젝트 템플릿에서 정의한 기본 태스크를 생성한다."""
    if not task_subjects:
        return []
    task_repo = _get_task_repo(tenant_id)
    generated_task_ids: list[str] = []
    for subject in task_subjects:
        task_id = generate_name(_TASK_PREFIX, tenant_id=tenant_id)
        task_repo.insert(
            Task(
                _id=task_id,
                tenant_id=tenant_id,
                subject=subject,
                project_ref=project_id,
                created_by=created_by,
                updated_by=created_by,
            )
        )
        generated_task_ids.append(task_id)
    return generated_task_ids


def _validate_project_manager(tenant_id: str, project_manager: str) -> None:
    """프로젝트 관리자로 지정한 직원이 존재하는지 검증한다."""
    if not project_manager:
        return
    if not _get_employee_repo(tenant_id).find_by_id(project_manager):
        raise_unprocessable("ERR-PRJ-010", "프로젝트 관리자 직원을 찾을 수 없습니다")


def _is_overdue_milestone(document: dict[str, Any]) -> bool:
    """마일스톤이 지연 상태인지 계산한다."""
    status = str(document.get("status", "")).lower()
    if status == "overdue":
        return True
    if status == "completed":
        return False
    due_date = document.get("due_date")
    if due_date is None:
        return False
    if isinstance(due_date, datetime):
        due = due_date.date()
    elif isinstance(due_date, date):
        due = due_date
    else:
        try:
            due = datetime.fromisoformat(str(due_date)).date()
        except ValueError:
            return False
    return due < datetime.now(tz=UTC).date()


def _build_listing_payload(
    tenant_id: str,
    projects: list[dict[str, Any]],
    *,
    status: str | None = None,
    company: str | None = None,
    project_manager: str | None = None,
) -> dict[str, Any]:
    """프로젝트 목록 카드와 요약 정보를 계산한다."""
    employee_docs = _get_employee_repo(tenant_id).find_many(limit=1000, sort=[("employee_name", 1)])
    task_docs = _get_task_repo(tenant_id).find_many(limit=5000, sort=[("created_at", -1)])
    milestone_docs = _get_milestone_repo(tenant_id).find_many(limit=5000, sort=[("due_date", 1)])

    employee_names = {
        document.get("_id", ""): document.get("employee_name", "")
        for document in employee_docs
        if document.get("_id")
    }
    task_count = Counter(
        document.get("project_ref", "") for document in task_docs if document.get("project_ref")
    )
    completed_task_count = Counter(
        document.get("project_ref", "")
        for document in task_docs
        if document.get("project_ref") and document.get("status") == "completed"
    )
    overdue_milestone_count = Counter(
        document.get("project", "")
        for document in milestone_docs
        if document.get("project") and _is_overdue_milestone(document)
    )

    rows: list[dict[str, Any]] = []
    for document in projects:
        row = _with_public_id(document)
        project_id = str(document.get("_id", ""))
        row["project_manager_name"] = employee_names.get(document.get("project_manager", ""), "")
        row["task_count"] = task_count.get(project_id, 0)
        row["completed_task_count"] = completed_task_count.get(project_id, 0)
        row["overdue_milestone_count"] = overdue_milestone_count.get(project_id, 0)
        rows.append(row)

    def _matches(row: dict[str, Any]) -> bool:
        if status and str(row.get("status", "")).lower() != status.lower():
            return False
        if company and row.get("company", "") != company:
            return False
        return not (project_manager and row.get("project_manager", "") != project_manager)

    rows = [row for row in rows if _matches(row)]

    total_budget = round(sum(float(row.get("budget", 0) or 0) for row in rows), 2)
    average_progress = 0.0
    if rows:
        average_progress = round(
            sum(float(row.get("percent_complete", 0) or 0) for row in rows) / len(rows),
            2,
        )
    status_counts = Counter(str(row.get("status", "open")).lower() for row in rows)
    return {
        "rows": rows,
        "summary": {
            "open": status_counts.get("open", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "completed": status_counts.get("completed", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "total_budget": total_budget,
            "average_progress": average_progress,
        },
    }


def _count_linked_submitted_timesheets(tenant_id: str, project_id: str) -> int:
    """제출된 타임시트 중 해당 프로젝트를 참조하는 문서 수를 센다."""
    timesheets = _get_timesheet_repo(tenant_id).find_many(limit=5000, sort=[("created_at", -1)])
    count = 0
    for document in timesheets:
        if document.get("docstatus", 0) != 1:
            continue
        time_logs = document.get("time_logs", []) or []
        if any(log.get("project_ref") == project_id for log in time_logs if isinstance(log, dict)):
            count += 1
    return count


@router.post("", status_code=201, dependencies=[Depends(require_permission("project:create"))])
def create_project(body: ProjectCreate, user: CurrentUserDep) -> dict[str, Any]:
    """프로젝트를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    payload = body.model_dump(exclude_none=True)
    _validate_project_manager(user.tenant_id, payload.get("project_manager", ""))
    template_tasks = _resolve_template_tasks(user.tenant_id, payload.get("template_id", ""))

    project = Project(
        _id=doc_id,
        tenant_id=user.tenant_id,
        project_name=body.project_name,
        expected_start_date=body.expected_start_date,
        expected_end_date=body.expected_end_date,
        company=body.company,
        cost_center=body.cost_center,
        customer=body.customer,
        project_manager=body.project_manager,
        budget=body.budget,
        template_id=body.template_id,
        generated_task_count=len(template_tasks),
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(project)
    generated_task_ids = _create_template_tasks(
        user.tenant_id,
        project_id=doc_id,
        task_subjects=template_tasks,
        created_by=user.sub,
    )
    return {
        "id": doc_id,
        "message": "프로젝트가 생성되었습니다",
        "generated_task_ids": generated_task_ids,
    }


@router.get("", dependencies=[Depends(require_permission("project:read"))])
def list_projects(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    company: str | None = None,
    project_manager: str | None = None,
) -> dict[str, Any]:
    """프로젝트 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if status:
        query["status"] = status
    if company:
        query["company"] = company
    if project_manager:
        query["project_manager"] = project_manager
    docs = repo.find_many(query, limit=1000, sort=[("created_at", -1)])
    payload = _build_listing_payload(
        user.tenant_id,
        docs,
        status=status,
        company=company,
        project_manager=project_manager,
    )
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": payload["rows"][start:end],
        "total": len(payload["rows"]),
        "page": page,
        "page_size": page_size,
        "summary": payload["summary"],
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("project:read"))])
def get_project(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """프로젝트 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("프로젝트를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    payload = _build_listing_payload(user.tenant_id, [doc])
    return payload["rows"][0]


@router.put("/{doc_id}", dependencies=[Depends(require_permission("project:write"))])
def update_project(
    doc_id: str,
    body: ProjectUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """프로젝트를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("프로젝트를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise_bad_request("수정할 내용이 없습니다")

    merged_start_date = update_data.get("expected_start_date", doc.get("expected_start_date"))
    merged_end_date = update_data.get("expected_end_date", doc.get("expected_end_date"))
    if (
        merged_start_date is not None
        and merged_end_date is not None
        and merged_end_date < merged_start_date
    ):
        raise_bad_request("예상 종료일은 예상 시작일보다 빠를 수 없습니다")
    if "project_manager" in update_data:
        _validate_project_manager(user.tenant_id, str(update_data.get("project_manager", "")))
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "프로젝트가 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("project:delete"))]
)
def delete_project(doc_id: str, user: CurrentUserDep) -> None:
    """프로젝트 삭제 — 타임시트/자식 문서가 남아 있으면 거부한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("프로젝트를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    if _count_linked_submitted_timesheets(user.tenant_id, doc_id) > 0:
        raise_bad_request("제출된 타임시트가 존재하여 프로젝트를 삭제할 수 없습니다")
    if (
        _get_task_repo(user.tenant_id).count({"project_ref": doc_id}) > 0
        or _get_milestone_repo(user.tenant_id).count({"project": doc_id}) > 0
        or _get_resource_allocation_repo(user.tenant_id).count({"project_id": doc_id}) > 0
        or _get_project_billing_repo(user.tenant_id).count({"project_id": doc_id}) > 0
    ):
        raise_unprocessable(
            "ERR-PRJ-011",
            "작업, 마일스톤, 자원 배정 또는 프로젝트 청구가 연결된 프로젝트는 삭제할 수 없습니다",
        )

    repo.delete_by_id(doc_id)
