"""RPA 작업(RPATask) CRUD + 실행/취소 라우트.

RPA 작업 생성, 목록 조회, 상세 조회, 수동 실행, 취소,
연결된 기기 목록 조회를 제공한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.rpa_task import RPATask, RPATaskCreate
from ..services.appium_manager import AppiumManager

router = APIRouter(prefix="/api/v1/rpa/tasks", tags=["RPA"])
_COLLECTION = "rpa_tasks"
_PREFIX = "RPAT"

logger = logging.getLogger(__name__)

# 싱글턴 AppiumManager — 서비스 전체에서 공유
_appium_manager = AppiumManager()

# 유효한 task_type 목록
_VALID_TASK_TYPES = frozenset(
    {
        "hometax_issue",
        "hometax_query",
        "banking_transactions",
        "banking_balance",
        "insurance_status",
    }
)


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("rpa_task:create"))],
)
async def create_rpa_task(body: RPATaskCreate, user: CurrentUserDep) -> dict:
    """RPA 작업을 생성한다."""
    if body.task_type not in _VALID_TASK_TYPES:
        msg = f"유효하지 않은 task_type: {body.task_type}"
        raise OneERPError(400, msg)

    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = RPATask(_id=doc_id, created_by=user.sub, **body.model_dump())
    repo.insert(doc)
    return {"task_id": doc_id, "message": "RPA 작업이 생성되었습니다"}


@router.get(
    "/",
    dependencies=[Depends(require_permission("rpa_task:read"))],
)
async def list_rpa_tasks(
    user: CurrentUserDep,
    status: str = "",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """RPA 작업 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict = {}
    if status:
        query["status"] = status
    skip = (page - 1) * page_size
    items = repo.find_many(query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count(query)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/devices",
    dependencies=[Depends(require_permission("rpa_task:read"))],
)
async def list_devices(_user: CurrentUserDep) -> dict:
    """연결된 Android 기기 목록을 반환한다."""
    devices = _appium_manager.get_connected_devices()
    return {"devices": devices, "count": len(devices)}


@router.get(
    "/{task_id}",
    dependencies=[Depends(require_permission("rpa_task:read"))],
)
async def get_rpa_task(task_id: str, user: CurrentUserDep) -> dict:
    """RPA 작업 상세를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(task_id)
    if not doc:
        msg = f"RPA 작업을 찾을 수 없음: {task_id}"
        raise OneERPError(404, msg)
    return doc


@router.post(
    "/{task_id}/run",
    dependencies=[Depends(require_permission("rpa_task:write"))],
)
async def run_rpa_task(task_id: str, user: CurrentUserDep) -> dict:
    """RPA 작업을 수동 실행한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(task_id)
    if not doc:
        msg = f"RPA 작업을 찾을 수 없음: {task_id}"
        raise OneERPError(404, msg)

    current_status = doc.get("status", "")
    if current_status not in ("pending", "failed"):
        msg = f"실행 가능한 상태가 아닙니다 (현재: {current_status})"
        raise OneERPError(400, msg)

    # 상태를 running으로 변경
    repo.update_by_id(
        task_id,
        {
            "status": "running",
            "started_at": datetime.now(tz=UTC),
            "error_message": "",
        },
    )

    logger.info("RPA 작업 실행 시작: %s (type=%s)", task_id, doc.get("task_type"))
    return {"task_id": task_id, "message": "RPA 작업 실행이 시작되었습니다"}


@router.post(
    "/{task_id}/cancel",
    dependencies=[Depends(require_permission("rpa_task:write"))],
)
async def cancel_rpa_task(task_id: str, user: CurrentUserDep) -> dict:
    """RPA 작업을 취소한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(task_id)
    if not doc:
        msg = f"RPA 작업을 찾을 수 없음: {task_id}"
        raise OneERPError(404, msg)

    current_status = doc.get("status", "")
    if current_status not in ("pending", "running"):
        msg = f"취소 가능한 상태가 아닙니다 (현재: {current_status})"
        raise OneERPError(400, msg)

    repo.update_by_id(
        task_id,
        {
            "status": "failed",
            "error_message": "사용자에 의해 취소됨",
            "completed_at": datetime.now(tz=UTC),
        },
    )

    logger.info("RPA 작업 취소: %s", task_id)
    return {"task_id": task_id, "message": "RPA 작업이 취소되었습니다"}
