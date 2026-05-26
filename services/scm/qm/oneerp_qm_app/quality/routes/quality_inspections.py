"""품질검사(QualityInspection) CRUD 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_qm_app.quality.models.quality_inspection import (
    QualityInspection,
    QualityInspectionCreate,
    QualityInspectionUpdate,
)

router = APIRouter(prefix="/api/v1/quality-inspections", tags=["품질검사"])

_COLLECTION = "quality_inspections"
_PREFIX = "QI"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("quality_inspection:create"))]
)
def create_quality_inspection(
    body: QualityInspectionCreate, user: CurrentUserDep
) -> dict[str, Any]:
    """품질검사를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    inspection = QualityInspection(
        _id=doc_id,
        tenant_id=user.tenant_id,
        reference_type=body.reference_type,
        reference_no=body.reference_no,
        inspection_type=body.inspection_type,
        item_code=body.item_code,
        readings=body.readings,
        result=body.result,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(inspection)
    return {"id": doc_id, "message": "품질검사가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("quality_inspection:read"))])
def list_quality_inspections(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """품질검사 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("quality_inspection:read"))])
def get_quality_inspection(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """품질검사 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("품질검사를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("quality_inspection:write"))])
def update_quality_inspection(
    doc_id: str,
    body: QualityInspectionUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """품질검사를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("품질검사를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise_bad_request("수정할 내용이 없습니다")
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "품질검사가 수정되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("quality_inspection:submit"))]
)
def submit_quality_inspection(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """품질검사를 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("품질검사를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    repo.submit_with_event(
        doc_id,
        event_type=EventType.QUALITY_INSPECTION_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "품질검사가 제출되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("quality_inspection:delete"))],
)
def delete_quality_inspection(doc_id: str, user: CurrentUserDep) -> None:
    """품질검사를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("품질검사를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    repo.delete_by_id(doc_id)
