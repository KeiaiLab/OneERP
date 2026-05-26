"""작업(Task) CRUD 라우터."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_projects_app.models.task import Task, TaskCreate, TaskStatus, TaskUpdate

router = APIRouter(prefix="/api/v1/tasks", tags=["작업"])

_COLLECTION = "tasks"
_PREFIX = "TASK"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_timesheet_repo(tenant_id: str) -> Repository:
    """작업 참조 삭제 제약 검사용 타임시트 저장소."""
    return Repository("timesheets", tenant_id=tenant_id)


def _build_task_query(
    *,
    status: TaskStatus | None,
    assigned_to: str | None,
    project_ref: str | None,
) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if status is not None:
        query["status"] = status.value
    if assigned_to:
        query["assigned_to"] = assigned_to
    if project_ref:
        query["project_ref"] = project_ref
    return query


def _validate_date_range(start_date: Any, end_date: Any) -> None:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise_bad_request("종료일은 시작일보다 빠를 수 없습니다")


def _ensure_predecessors_completed(
    repo: Repository,
    predecessor_task_ids: list[str],
    current_task_id: str,
) -> None:
    if not predecessor_task_ids:
        return

    for predecessor_task_id in predecessor_task_ids:
        if predecessor_task_id == current_task_id:
            raise_bad_request("작업은 자기 자신을 선행 작업으로 지정할 수 없습니다")
        predecessor = repo.find_by_id(predecessor_task_id)
        if not predecessor or predecessor.get("status") != TaskStatus.COMPLETED.value:
            raise_bad_request("선행 작업이 완료되어야 합니다")


def _validate_status_transition(
    repo: Repository,
    doc_id: str,
    current_doc: dict[str, Any],
    update_data: dict[str, Any],
) -> None:
    next_status = update_data.get("status")
    if next_status is None:
        return

    merged_assigned_to = str(
        update_data.get("assigned_to", current_doc.get("assigned_to", ""))
    ).strip()
    merged_predecessors = [
        predecessor
        for predecessor in update_data.get(
            "predecessor_task_ids",
            current_doc.get("predecessor_task_ids", []),
        )
        if predecessor
    ]
    merged_actual_time = Decimal(
        str(update_data.get("actual_time", current_doc.get("actual_time", 0)))
    )
    current_status = TaskStatus(str(current_doc.get("status", TaskStatus.OPEN.value)))

    if next_status in {TaskStatus.WORKING, TaskStatus.PENDING_REVIEW, TaskStatus.COMPLETED}:
        _ensure_predecessors_completed(repo, merged_predecessors, doc_id)

    if next_status == TaskStatus.WORKING and not merged_assigned_to:
        raise_unprocessable("ERR-PRJ-012", "담당자가 지정된 작업만 진행중으로 전환할 수 있습니다")

    if next_status == TaskStatus.PENDING_REVIEW and merged_actual_time <= 0:
        raise_unprocessable(
            "ERR-PRJ-013", "실제 시간이 기록된 작업만 검토 대기로 전환할 수 있습니다"
        )

    if next_status == TaskStatus.COMPLETED and current_status != TaskStatus.PENDING_REVIEW:
        raise_unprocessable("ERR-PRJ-014", "검토 대기 상태의 작업만 완료 처리할 수 있습니다")


@router.post("", status_code=201, dependencies=[Depends(require_permission("task:create"))])
def create_task(body: TaskCreate, user: CurrentUserDep) -> dict[str, Any]:
    """작업을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    task = Task(
        _id=doc_id,
        tenant_id=user.tenant_id,
        subject=body.subject,
        project_ref=body.project_ref,
        assigned_to=body.assigned_to,
        priority=body.priority,
        start_date=body.start_date,
        end_date=body.end_date,
        predecessor_task_ids=body.predecessor_task_ids,
        expected_time=body.expected_time,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(task)
    return {"id": doc_id, "message": "작업이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("task:read"))])
def list_tasks(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: TaskStatus | None = None,
    assigned_to: str | None = None,
    project_ref: str | None = None,
) -> dict[str, Any]:
    """작업 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    query = _build_task_query(
        status=status,
        assigned_to=assigned_to,
        project_ref=project_ref,
    )
    docs = repo.find_many(query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count(query)
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("task:read"))])
def get_task(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """작업 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("task:write"))])
def update_task(
    doc_id: str,
    body: TaskUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """작업을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise_bad_request("수정할 내용이 없습니다")

    merged_start_date = update_data.get("start_date", doc.get("start_date"))
    merged_end_date = update_data.get("end_date", doc.get("end_date"))
    _validate_date_range(merged_start_date, merged_end_date)

    _validate_status_transition(repo, doc_id, doc, update_data)

    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "작업이 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("task:delete"))]
)
def delete_task(doc_id: str, user: CurrentUserDep) -> None:
    """작업을 삭제한다. 후속 작업/타임시트 참조가 없을 때만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("작업을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    has_successors = bool(repo.find_many({"predecessor_task_ids": doc_id}, limit=1))
    has_timesheet_logs = bool(
        _get_timesheet_repo(user.tenant_id).find_many({"time_logs.task_ref": doc_id}, limit=1)
    )
    if has_successors or has_timesheet_logs:
        raise_unprocessable(
            "ERR-PRJ-015",
            "선행 작업으로 연결되었거나 타임시트 로그가 남아 있는 작업은 삭제할 수 없습니다",
        )

    repo.delete_by_id(doc_id)
