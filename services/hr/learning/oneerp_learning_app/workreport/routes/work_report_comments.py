"""업무일지 코멘트(WorkReportComment) 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..services.work_report_service import WorkReportService

router = APIRouter(prefix="/api/v1/work-report-comments", tags=["업무일지코멘트"])
_COLLECTION = "work_report_comments"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("work_report_comment:create"))],
)
async def create_comment(
    work_report_id: str,
    content: str,
    user: CurrentUserDep,
) -> dict:
    """업무일지에 코멘트를 추가한다.

    BR-WR-020: 제출된 업무일지에만 코멘트 가능.
    BR-WR-021: 코멘트 내용 필수.
    """
    service = WorkReportService(tenant_id="default")
    result = service.add_comment(
        report_id=work_report_id,
        author_id=user.sub,
        author_name="",
        content=content,
    )
    return {"message": "코멘트가 추가되었습니다", **result}


@router.get(
    "/{work_report_id}",
    dependencies=[Depends(require_permission("work_report_comment:read"))],
)
async def list_comments(work_report_id: str) -> dict:
    """업무일지의 코멘트 목록을 조회한다."""
    repo = _get_repo()
    data = repo.find_many(
        {"work_report_id": work_report_id},
        sort=[("created_at", 1)],
        limit=100,
    )
    return {"data": data, "total": len(data)}
