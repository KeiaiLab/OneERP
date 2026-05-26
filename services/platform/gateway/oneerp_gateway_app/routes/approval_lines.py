"""결재라인(ApprovalLine) CRUD 라우트."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.approval_line import ApprovalLine, ApprovalLineCreate, ApprovalLineUpdate

router = APIRouter(prefix="/api/v1/approval-lines", tags=["결재라인"])
_COLLECTION = "approval_lines"
_PREFIX = "AL"


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _build_query(
    *,
    template: str | None = None,
    approver: str | None = None,
    approver_role: str | None = None,
    approval_type: str | None = None,
    sequence: int | None = None,
    pre_approval_enabled: bool | None = None,
) -> dict:
    query: dict = {}
    if template:
        query["template"] = template
    if approver:
        query["approver"] = approver
    if approver_role:
        query["approver_role"] = approver_role
    if approval_type:
        query["approval_type"] = approval_type
    if sequence is not None:
        query["sequence"] = sequence
    if pre_approval_enabled is True:
        query["pre_approval_roles.0"] = {"$exists": True}
    elif pre_approval_enabled is False:
        query["$or"] = [
            {"pre_approval_roles": []},
            {"pre_approval_roles": {"$exists": False}},
        ]
    return query


def _load_same_step_lines(
    repo: Repository,
    *,
    template: str,
    sequence: int,
    exclude_id: str | None = None,
) -> list[dict]:
    rows = repo.find_many(
        {"template": template, "sequence": sequence},
        sort=[("sequence", 1), ("created_at", 1)],
        limit=1000,
    )
    if exclude_id:
        return [row for row in rows if row.get("_id") != exclude_id]
    return rows


def _validate_payload(
    payload: ApprovalLineCreate | ApprovalLineUpdate,
    *,
    repo: Repository | None = None,
    current_doc_id: str | None = None,
) -> None:
    sequence = getattr(payload, "sequence", None)
    if sequence is not None and sequence < 1:
        raise OneERPError(
            status_code=422,
            error="invalid_sequence",
            detail="결재선 순서는 1 이상이어야 합니다",
        )

    approver = (getattr(payload, "approver", None) or "").strip()
    approver_role = (getattr(payload, "approver_role", None) or "").strip()
    if not approver and not approver_role:
        raise OneERPError(
            status_code=422,
            error="invalid_approver",
            detail="결재자 또는 결재자 역할 중 하나는 반드시 지정해야 합니다",
        )

    approval_type = getattr(payload, "approval_type", None)
    if approval_type is not None and approval_type not in {"single", "consensus"}:
        raise OneERPError(
            status_code=422,
            error="invalid_approval_type",
            detail="approval_type은 single 또는 consensus만 허용됩니다",
        )

    template = (getattr(payload, "template", None) or "").strip()
    if not repo or not template or sequence is None:
        return

    same_step_lines = _load_same_step_lines(
        repo,
        template=template,
        sequence=sequence,
        exclude_id=current_doc_id,
    )
    for line in same_step_lines:
        if approver and approver == line.get("approver", ""):
            raise OneERPError(
                status_code=422,
                error="ERR-APR-010",
                detail="같은 단계에는 동일한 결재자를 중복 등록할 수 없습니다",
            )
        if approver_role and approver_role == line.get("approver_role", ""):
            raise OneERPError(
                status_code=422,
                error="ERR-APR-010",
                detail="같은 단계에는 동일한 결재자 역할을 중복 등록할 수 없습니다",
            )

    normalized_type = approval_type or "single"
    if same_step_lines and normalized_type != "consensus":
        raise OneERPError(
            status_code=422,
            error="ERR-APR-011",
            detail="같은 단계에 여러 결재선을 두려면 approval_type은 consensus여야 합니다",
        )

    existing_types = {line.get("approval_type", "single") for line in same_step_lines}
    if existing_types and normalized_type not in existing_types:
        raise OneERPError(
            status_code=422,
            error="ERR-APR-011",
            detail="같은 단계의 결재선은 동일한 approval_type만 사용할 수 있습니다",
        )


def _build_step_summary(doc: dict, same_step_lines: list[dict]) -> dict:
    condition_values = {
        str(line.get("condition", "")).strip()
        for line in same_step_lines
        if str(line.get("condition", "")).strip()
    }
    approval_mode = (
        "consensus"
        if len(same_step_lines) > 1
        or any(line.get("approval_type") == "consensus" for line in same_step_lines)
        else "single"
    )
    return {
        "template": doc.get("template", ""),
        "sequence": int(doc.get("sequence", 0)),
        "approver_count": len(same_step_lines),
        "approval_mode": approval_mode,
        "pre_approval_enabled": any(line.get("pre_approval_roles") for line in same_step_lines),
        "condition": " / ".join(sorted(condition_values)),
    }


def _serialize_approval_line(doc: dict, same_step_lines: list[dict]) -> dict:
    serialized = dict(doc)
    step_summary = _build_step_summary(doc, same_step_lines)
    badge = step_summary["approval_mode"]
    if badge == "single" and step_summary["pre_approval_enabled"]:
        badge = "single_pre_approval"
    serialized["approval_mode_badge"] = badge
    serialized["step_summary"] = step_summary
    serialized["available_actions"] = ["edit", "reorder", "delete"]
    return serialized


def _build_workbench_summary(lines: list[dict]) -> dict:
    unique_templates = {line.get("template", "") for line in lines if line.get("template")}
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for line in lines:
        groups[(line.get("template", ""), int(line.get("sequence", 0)))].append(line)

    return {
        "template_count": len(unique_templates),
        "step_count": len(groups),
        "consensus_step_count": sum(
            1
            for rows in groups.values()
            if len(rows) > 1 or any(row.get("approval_type") == "consensus" for row in rows)
        ),
        "pre_approval_step_count": sum(
            1 for rows in groups.values() if any(row.get("pre_approval_roles") for row in rows)
        ),
        "conditional_step_count": sum(
            1
            for rows in groups.values()
            if any(str(row.get("condition", "")).strip() for row in rows)
        ),
    }


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("approval_line:create"))]
)
async def create_approval_line(body: ApprovalLineCreate, user: CurrentUserDep) -> dict:
    """결재라인을 생성한다."""
    repo = _get_repo(user.tenant_id)
    _validate_payload(body, repo=repo)
    doc_id = generate_name(_PREFIX)
    doc = ApprovalLine(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"approval_line_id": doc_id, "message": "결재라인이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("approval_line:read"))])
async def list_approval_lines(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    template: str | None = None,
    approver: str | None = None,
    approver_role: str | None = None,
    approval_type: str | None = None,
    sequence: int | None = None,
    *,
    pre_approval_enabled: bool | None = None,
) -> dict:
    """결재라인 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    query = _build_query(
        template=template,
        approver=approver,
        approver_role=approver_role,
        approval_type=approval_type,
        sequence=sequence,
        pre_approval_enabled=pre_approval_enabled,
    )
    total = repo.count(query)
    rows = repo.find_many(
        query,
        skip=0,
        limit=max(total, page_size, 1),
        sort=[("sequence", 1), ("created_at", 1)],
    )

    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row.get("template", ""), int(row.get("sequence", 0)))].append(row)
    serialized = [
        _serialize_approval_line(
            row, groups[(row.get("template", ""), int(row.get("sequence", 0)))]
        )
        for row in rows
    ]
    skip = (page - 1) * page_size
    return {
        "data": serialized[skip : skip + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_workbench_summary(rows),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("approval_line:read"))])
async def get_approval_line(doc_id: str, user: CurrentUserDep) -> dict:
    """결재라인 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재라인을 찾을 수 없습니다")
    same_step_lines = _load_same_step_lines(
        repo,
        template=doc.get("template", ""),
        sequence=int(doc.get("sequence", 0)),
    )
    return _serialize_approval_line(doc, same_step_lines)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("approval_line:write"))])
async def update_approval_line(doc_id: str, body: ApprovalLineUpdate, user: CurrentUserDep) -> dict:
    """결재라인을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재라인을 찾을 수 없습니다")
    merged = {**doc, **body.model_dump(exclude_none=True)}
    _validate_payload(ApprovalLineCreate(**merged), repo=repo, current_doc_id=doc_id)
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "결재라인이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("approval_line:delete"))])
async def delete_approval_line(doc_id: str, user: CurrentUserDep) -> dict:
    """결재라인을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재라인을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "결재라인이 삭제되었습니다"}
