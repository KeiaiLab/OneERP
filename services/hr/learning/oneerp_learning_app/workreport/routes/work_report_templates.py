"""업무일지 템플릿(WorkReportTemplate) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.work_report_template import (
    WorkReportTemplate,
    WorkReportTemplateCreate,
    WorkReportTemplateUpdate,
)

router = APIRouter(prefix="/api/v1/work-report-templates", tags=["업무일지템플릿"])
_COLLECTION = "work_report_templates"
_PREFIX = "WRT"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("work_report_template:create"))],
)
async def create_template(body: WorkReportTemplateCreate) -> dict:
    """업무일지 템플릿을 생성한다.

    BR-WR-010: 템플릿명 필수 (모델 required 필드로 검증).
    """
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = WorkReportTemplate(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"id": doc_id, "message": "업무일지 템플릿이 생성되었습니다"}


@router.get(
    "/",
    dependencies=[Depends(require_permission("work_report_template:read"))],
)
async def list_templates(page: int = 1, page_size: int = 20) -> dict:
    """업무일지 템플릿 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{doc_id}",
    dependencies=[Depends(require_permission("work_report_template:read"))],
)
async def get_template(doc_id: str) -> dict:
    """업무일지 템플릿 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="업무일지 템플릿을 찾을 수 없습니다",
        )
    return doc


@router.put(
    "/{doc_id}",
    dependencies=[Depends(require_permission("work_report_template:write"))],
)
async def update_template(doc_id: str, body: WorkReportTemplateUpdate) -> dict:
    """업무일지 템플릿을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="업무일지 템플릿을 찾을 수 없습니다",
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "업무일지 템플릿이 수정되었습니다"}
