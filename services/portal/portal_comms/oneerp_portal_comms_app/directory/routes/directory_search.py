"""인명부 검색 API 라우터 — 직원 검색/필터링/배치 등록."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from oneerp_portal_comms_app.directory.services.directory_search_service import (
    DirectorySearchService,
)

router = APIRouter(prefix="/api/v1/directory-search", tags=["인명부검색"])


class BatchRegisterRequest(BaseModel):
    """인명부 배치 등록 요청 스키마."""

    entries: list[dict[str, Any]]


def _get_service(tenant_id: str) -> DirectorySearchService:
    """현재 사용자의 tenant에 바인딩된 서비스를 반환한다."""
    return DirectorySearchService(tenant_id=tenant_id)


@router.get(
    "",
    dependencies=[Depends(require_permission("employee_directory:read"))],
)
def search_directory(
    user: CurrentUserDep,
    keyword: str = "",
    org_unit_id: str = "",
    designation: str = "",
    status: str = "active",
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """인명부를 검색한다."""
    svc = _get_service(user.tenant_id)
    return svc.search_directory(
        keyword=keyword,
        org_unit_id=org_unit_id,
        designation=designation,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/units/{org_unit_id}/members",
    dependencies=[Depends(require_permission("employee_directory:read"))],
)
def get_unit_members(
    org_unit_id: str,
    user: CurrentUserDep,
    include_sub_units: str = "",
) -> list[dict[str, Any]]:
    """조직 단위의 소속 직원 목��을 ��회한다."""
    svc = _get_service(user.tenant_id)
    return svc.get_unit_members(
        org_unit_id,
        include_sub_units=include_sub_units.lower() in ("true", "1", "yes"),
    )


@router.post(
    "/batch",
    status_code=201,
    dependencies=[Depends(require_permission("employee_directory:create"))],
)
def batch_register(
    body: BatchRegisterRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """인명부를 배치로 등록한다."""
    if not body.entries:
        raise_bad_request("ERR-DIR-015: 등록할 엔트리가 없습니다")
    svc = _get_service(user.tenant_id)
    return svc.batch_register(body.entries)
