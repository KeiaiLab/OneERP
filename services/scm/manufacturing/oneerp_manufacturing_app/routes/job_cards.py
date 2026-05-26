"""작업카드(JobCard) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.job_card import JobCard, JobCardCreate, JobCardUpdate

router = APIRouter(prefix="/api/v1/job-cards", tags=["작업카드"])

_COLLECTION = "job_cards"
_PREFIX = "JC"


def _get_repo() -> Repository:
    """작업카드 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.post("", status_code=201, dependencies=[Depends(require_permission("job_card:create"))])
def create_job_card(body: JobCardCreate) -> dict:
    """작업카드를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = JobCard(
        work_order=body.work_order,
        operation=body.operation,
        workstation=body.workstation,
        employee_id=body.employee_id,
        status=body.status,
        planned_time=body.planned_time,
        actual_time=body.actual_time,
        started_at=body.started_at,
        completed_at=body.completed_at,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "작업카드가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("job_card:read"))])
def list_job_cards(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """작업카드 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("job_card:read"))])
def get_job_card(doc_id: str) -> dict:
    """작업카드를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업카드를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("job_card:write"))])
def update_job_card(doc_id: str, body: JobCardUpdate) -> dict:
    """작업카드를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업카드를 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "작업카드가 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=200, dependencies=[Depends(require_permission("job_card:delete"))]
)
def delete_job_card(doc_id: str) -> dict:
    """작업카드를 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업카드를 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"id": doc_id, "message": "작업카드가 삭제되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("job_card:submit"))])
def submit_job_card(doc_id: str, user: CurrentUserDep) -> dict:
    """작업카드를 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업카드를 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400, error="invalid_status", detail="초안 상태에서만 제출 가능"
        )
    repo.submit_with_event(
        doc_id,
        event_type=EventType.JOB_CARD_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"message": "작업카드가 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("job_card:cancel"))])
def cancel_job_card(doc_id: str) -> dict:
    """작업카드를 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="작업카드를 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(status_code=400, error="invalid_status", detail="제출된 문서만 취소 가능")
    repo.cancel(doc_id)
    return {"message": "작업카드가 취소되었습니다"}
