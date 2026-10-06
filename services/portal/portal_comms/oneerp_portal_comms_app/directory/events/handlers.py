"""조직도/인명부 이벤트 핸들러 — 타 서비스 이벤트 수신 처리.

HR 서비스의 직원 변경 이벤트를 수신하여 인명부를 자동 갱신한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


def handle_employee_updated(event_data: dict[str, Any]) -> None:
    """HR 서비스의 직원 정보 변경 이벤트를 처리한다.

    직원명, 이메일 등 기본 정보가 변경되면 인명부 엔트리를 갱신한다.

    Args:
        event_data: 이벤트 페이로드
    """
    tenant_id = event_data.get("tenant_id", "")
    employee_id = event_data.get("employee_id", "")

    if not employee_id:
        logger.warning("직원 ID가 누락된 이벤트 수신")
        return

    dir_repo = Repository("employee_directories", tenant_id=tenant_id)
    entries = dir_repo.find_many(
        {"employee_id": employee_id},
        limit=100,
    )

    update_fields: dict[str, Any] = {}
    if "employee_name" in event_data:
        update_fields["employee_name"] = event_data["employee_name"]
    if "email" in event_data:
        update_fields["email"] = event_data["email"]
    if "phone" in event_data:
        update_fields["phone"] = event_data["phone"]
    if "mobile" in event_data:
        update_fields["mobile"] = event_data["mobile"]

    if not update_fields:
        return

    updated_count = 0
    for entry in entries:
        entry_id = entry.get("_id", "")
        if entry_id:
            dir_repo.update_by_id(entry_id, update_fields)
            updated_count += 1

    logger.info(
        "직원 정보 변경 반영: 인명부 %d건 갱신",
        updated_count,
    )
