"""품질검사템플릿(QualityInspectionTemplate) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.quality_inspection_template import (
    QualityInspectionTemplate,
    QualityInspectionTemplateCreate,
    QualityInspectionTemplateUpdate,
)

router = APIRouter(prefix="/api/v1/quality-inspection-templates", tags=["품질검사템플릿"])
_COLLECTION = "quality_inspection_templates"
_PREFIX = "QITM"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("quality_inspection_template:create"))],
)
async def create_quality_inspection_template(body: QualityInspectionTemplateCreate) -> dict:
    """품질검사템플릿을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = QualityInspectionTemplate(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"quality_inspection_template_id": doc_id, "message": "품질검사템플릿이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("quality_inspection_template:read"))])
async def list_quality_inspection_templates(page: int = 1, page_size: int = 20) -> dict:
    """품질검사템플릿 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{doc_id}", dependencies=[Depends(require_permission("quality_inspection_template:read"))]
)
async def get_quality_inspection_template(doc_id: str) -> dict:
    """품질검사템플릿 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="품질검사템플릿을 찾을 수 없습니다"
        )
    return doc


@router.put(
    "/{doc_id}", dependencies=[Depends(require_permission("quality_inspection_template:write"))]
)
async def update_quality_inspection_template(
    doc_id: str, body: QualityInspectionTemplateUpdate
) -> dict:
    """품질검사템플릿을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="품질검사템플릿을 찾을 수 없습니다"
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "품질검사템플릿이 수정되었습니다"}


@router.delete(
    "/{doc_id}", dependencies=[Depends(require_permission("quality_inspection_template:delete"))]
)
async def delete_quality_inspection_template(doc_id: str) -> dict:
    """품질검사템플릿을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="품질검사템플릿을 찾을 수 없습니다"
        )
    repo.delete_by_id(doc_id)
    return {"message": "품질검사템플릿이 삭제되었습니다"}
