"""계정과목 CRUD 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import (
    delete_draft,
    get_or_404,
    paginated_list,
)

from oneerp_accounting_app.models.account import Account, AccountCreate, AccountUpdate

router = APIRouter(prefix="/api/v1/accounts", tags=["계정과목"])

_COLLECTION = "accounts"
_PREFIX = "ACC"
_NOT_FOUND = "계정과목을 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("account:create"))])
def create_account(body: AccountCreate, user: CurrentUserDep) -> dict[str, Any]:
    """계정과목을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    account = Account(
        _id=doc_id,
        tenant_id=user.tenant_id,
        account_name=body.account_name,
        account_type=body.account_type,
        parent_account=body.parent_account,
        is_group=body.is_group,
        currency=body.currency,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(account)
    return {"id": doc_id, "message": "계정과목 생성 완료"}


@router.get("", dependencies=[Depends(require_permission("account:read"))])
def list_accounts(
    user: CurrentUserDep,
    parent: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """계정과목 목록을 조회한다. parent 파라미터로 트리 구조를 지원한다."""
    repo = _get_repo(user.tenant_id)
    filter_query: dict[str, Any] = {}
    if parent is not None:
        filter_query["parent_account"] = parent
    return paginated_list(repo, page, page_size, filter_query=filter_query)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("account:read"))])
def get_account(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """계정과목을 조회한다."""
    repo = _get_repo(user.tenant_id)
    return get_or_404(repo, doc_id, _NOT_FOUND)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("account:write"))])
def update_account(doc_id: str, body: AccountUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """계정과목을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {**doc, **update_data}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("account:delete"))]
)
def delete_account(doc_id: str, user: CurrentUserDep) -> None:
    """계정과목을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND)
