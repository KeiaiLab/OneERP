"""결재템플릿(ApprovalTemplate) CRUD 라우트."""

from __future__ import annotations

from copy import deepcopy

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel

from ..models.approval_template import (
    APPROVAL_TEMPLATE_PRESETS,
    ApprovalTemplate,
    ApprovalTemplateCreate,
    ApprovalTemplateUpdate,
)

router = APIRouter(prefix="/api/v1/approval-templates", tags=["결재템플릿"])
_COLLECTION = "approval_templates"
_APPROVAL_LINE_COLLECTION = "approval_lines"
_PREFIX = "AT"
_ALLOWED_FIELD_TYPES = {"text", "textarea", "date", "select", "currency", "attachment"}


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_approval_line_repo(tenant_id: str = "") -> Repository:
    """결재선 마스터 저장소를 반환한다."""
    return Repository(_APPROVAL_LINE_COLLECTION, tenant_id=tenant_id)


class ApprovalTemplatePresetCreateBody(BaseModel):
    """프리셋 기반 결재템플릿 생성 요청."""

    template_name: str | None = None
    description: str | None = None


class ApprovalTemplateCloneBody(BaseModel):
    """결재템플릿 복제 요청."""

    template_name: str | None = None


def _validate_steps(steps: list | None) -> None:
    """결재 단계 배열의 최소 유효성을 검사한다."""
    if steps is None:
        return
    if not steps:
        raise OneERPError(
            status_code=422,
            error="invalid_template",
            detail="결재 단계가 없습니다",
        )

    step_numbers: list[int] = []
    for step in steps:
        step_no = step.step if hasattr(step, "step") else int(step.get("step", 0))
        approval_type = (
            step.approval_type
            if hasattr(step, "approval_type")
            else step.get("approval_type", "single")
        )
        approver = step.approver if hasattr(step, "approver") else step.get("approver", "")
        approver_role = (
            step.approver_role if hasattr(step, "approver_role") else step.get("approver_role", "")
        )
        approvers = step.approvers if hasattr(step, "approvers") else step.get("approvers", [])
        if step_no < 1:
            raise OneERPError(
                status_code=422,
                error="invalid_template",
                detail="결재 단계 번호는 1 이상이어야 합니다",
            )
        if approval_type == "consensus" and not (approvers or approver or approver_role):
            raise OneERPError(
                status_code=422,
                error="invalid_template",
                detail="합의 결재 단계에는 결재자를 지정해야 합니다",
            )
        if approval_type != "consensus" and not (approver or approver_role):
            raise OneERPError(
                status_code=422,
                error="invalid_template",
                detail="단일 결재 단계에는 approver 또는 approver_role이 필요합니다",
            )
        step_numbers.append(step_no)

    ordered = sorted(step_numbers)
    expected = list(range(1, len(ordered) + 1))
    if ordered != expected:
        raise OneERPError(
            status_code=422,
            error="invalid_template",
            detail="결재 단계 번호는 1부터 중복 없이 연속되어야 합니다",
        )


def _validate_form_fields(form_fields: list | None) -> None:
    """양식 필드 중복과 지원 타입을 검증한다."""
    if not form_fields:
        return

    seen_keys: set[str] = set()
    for field in form_fields:
        field_key = (
            field.field_key
            if hasattr(field, "field_key")
            else str(field.get("field_key", "")).strip()
        )
        field_type = (
            field.field_type if hasattr(field, "field_type") else field.get("field_type", "text")
        )

        if not field_key:
            raise OneERPError(
                status_code=422,
                error="ERR-APR-006",
                detail="양식 필드 키는 비어 있을 수 없습니다",
            )
        if field_key in seen_keys:
            raise OneERPError(
                status_code=422,
                error="ERR-APR-006",
                detail="양식 필드 키는 중복될 수 없습니다",
            )
        if field_type not in _ALLOWED_FIELD_TYPES:
            raise OneERPError(
                status_code=422,
                error="ERR-APR-006",
                detail=f"지원하지 않는 양식 필드 유형입니다: {field_type}",
            )
        seen_keys.add(field_key)


def _validate_data_binding_fields(binding_fields: list | None) -> None:
    """데이터 바인딩 대상 필드 중복을 검증한다."""
    if not binding_fields:
        return

    seen_targets: set[str] = set()
    for binding in binding_fields:
        target_field = (
            binding.target_field
            if hasattr(binding, "target_field")
            else str(binding.get("target_field", "")).strip()
        )
        if not target_field:
            raise OneERPError(
                status_code=422,
                error="ERR-APR-007",
                detail="데이터 바인딩 대상 필드는 비어 있을 수 없습니다",
            )
        if target_field in seen_targets:
            raise OneERPError(
                status_code=422,
                error="ERR-APR-007",
                detail="데이터 바인딩 대상 필드는 중복될 수 없습니다",
            )
        seen_targets.add(target_field)


def _validate_template_payload(
    steps: list | None,
    form_fields: list | None,
    data_binding_fields: list | None,
) -> None:
    _validate_steps(steps)
    _validate_form_fields(form_fields)
    _validate_data_binding_fields(data_binding_fields)


def _get_preset(preset_code: str) -> dict:
    """프리셋 코드를 기준으로 정의를 반환한다."""
    for preset in APPROVAL_TEMPLATE_PRESETS:
        if preset["preset_code"] == preset_code:
            return deepcopy(preset)
    raise OneERPError(
        status_code=404, error="not_found", detail="결재 양식 프리셋을 찾을 수 없습니다"
    )


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("approval_template:create"))]
)
async def create_approval_template(body: ApprovalTemplateCreate, user: CurrentUserDep) -> dict:
    """결재템플릿을 생성한다."""
    _validate_template_payload(body.steps, body.form_fields, body.data_binding_fields)
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = ApprovalTemplate(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"approval_template_id": doc_id, "message": "결재템플릿이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("approval_template:read"))])
async def list_approval_templates(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    document_type: str | None = None,
    *,
    is_active: bool | None = None,
) -> dict:
    """결재템플릿 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict = {}
    if document_type:
        query["document_type"] = document_type
    if is_active is not None:
        query["is_active"] = is_active
    skip = (page - 1) * page_size
    data = repo.find_many(query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count(query)
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/presets", dependencies=[Depends(require_permission("approval_template:read"))])
async def list_approval_template_presets(_user: CurrentUserDep) -> dict:
    """기본 결재 양식 프리셋을 조회한다."""
    data = [deepcopy(preset) for preset in APPROVAL_TEMPLATE_PRESETS]
    return {"data": data, "total": len(data)}


@router.post(
    "/presets/{preset_code}",
    status_code=201,
    dependencies=[Depends(require_permission("approval_template:create"))],
)
async def create_approval_template_from_preset(
    preset_code: str,
    body: ApprovalTemplatePresetCreateBody,
    user: CurrentUserDep,
) -> dict:
    """기본 프리셋으로 결재템플릿을 생성한다."""
    preset = _get_preset(preset_code)
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    preset["template_name"] = body.template_name or preset["template_name"]
    preset["description"] = body.description or preset["description"]
    preset["template_code"] = preset.pop("preset_code")
    _validate_template_payload(
        preset["steps"],
        preset.get("form_fields"),
        preset.get("data_binding_fields"),
    )
    doc = ApprovalTemplate(_id=doc_id, **preset)
    repo.insert(doc)
    return {
        "approval_template_id": doc_id,
        "message": "결재템플릿 프리셋이 생성되었습니다",
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("approval_template:read"))])
async def get_approval_template(doc_id: str, user: CurrentUserDep) -> dict:
    """결재템플릿 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="결재템플릿을 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("approval_template:write"))])
async def update_approval_template(
    doc_id: str, body: ApprovalTemplateUpdate, user: CurrentUserDep
) -> dict:
    """결재템플릿을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="결재템플릿을 찾을 수 없습니다"
        )
    payload = {**doc, **body.model_dump(exclude_none=True)}
    _validate_template_payload(
        payload.get("steps"),
        payload.get("form_fields"),
        payload.get("data_binding_fields"),
    )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "결재템플릿이 수정되었습니다"}


@router.post(
    "/{doc_id}/clone",
    status_code=201,
    dependencies=[Depends(require_permission("approval_template:create"))],
)
async def clone_approval_template(
    doc_id: str,
    body: ApprovalTemplateCloneBody,
    user: CurrentUserDep,
) -> dict:
    """기존 결재 양식을 복제해 새 템플릿을 만든다."""
    repo = _get_repo(user.tenant_id)
    source = repo.find_by_id(doc_id)
    if not source:
        raise OneERPError(
            status_code=404, error="not_found", detail="결재템플릿을 찾을 수 없습니다"
        )

    payload = deepcopy(source)
    payload.pop("_id", None)
    payload.pop("id", None)
    payload["template_name"] = (
        body.template_name or f"{source.get('template_name', '결재 양식')} 복사본"
    )
    _validate_template_payload(
        payload.get("steps"),
        payload.get("form_fields"),
        payload.get("data_binding_fields"),
    )
    new_doc_id = generate_name(_PREFIX)
    repo.insert(ApprovalTemplate(_id=new_doc_id, **payload))
    return {"approval_template_id": new_doc_id, "message": "결재템플릿이 복제되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("approval_template:delete"))])
async def delete_approval_template(doc_id: str, user: CurrentUserDep) -> dict:
    """결재템플릿을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="결재템플릿을 찾을 수 없습니다"
        )
    approval_line_repo = _get_approval_line_repo(user.tenant_id)
    if approval_line_repo.count({"template": doc_id}) > 0:
        raise OneERPError(
            status_code=422,
            error="ERR-APR-008",
            detail="결재선 마스터가 연결된 결재템플릿은 삭제할 수 없습니다",
        )
    repo.delete_by_id(doc_id)
    return {"message": "결재템플릿이 삭제되었습니다"}
