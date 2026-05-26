"""인사이동 서비스 — 부서/직위 이동 처리 및 히스토리 관리 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-HR-007: 인사이동 이력 자동 기록 (이전 부서/직위 + 직원 마스터 갱신)
- BR-HR-009: EMPLOYEE_UPDATED 이벤트 발행 (직원 정보 변경 시)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.events.outbox import OutboxMixin
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class TransferService:
    """인사이동(Employee Transfer) 비즈니스 로직.

    부서/직위 이동을 처리하고 직원 마스터를 자동 업데이트한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._transfer_repo = Repository("employee_transfers", tenant_id=tenant_id)
        self._employee_repo = Repository("employees", tenant_id=tenant_id)

    def execute_transfer(
        self,
        employee: str,
        new_department: str = "",
        new_designation: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        """인사이동을 실행한다.

        직원 마스터의 부서/직위를 업데이트하고 이동 기록을 생성한다.

        Args:
            employee: 직원 ID
            new_department: 이동 후 부서 (비어있으면 변경 안 함)
            new_designation: 이동 후 직위 (비어있으면 변경 안 함)
            reason: 이동 사유

        Returns:
            이동 결과 (transfer_id, changes)
        """
        emp = self._employee_repo.find_by_id(employee)
        if not emp:
            raise_not_found(f"직원 '{employee}'을 찾을 수 없습니다")

        if not new_department and not new_designation:
            raise_unprocessable("ERR-HR-003", "부서 또는 직위 중 1개 이상 변경해야 합니다")

        old_department = emp.get("department", "")
        old_designation = emp.get("designation", "")

        # 이동 기록 생성
        transfer_id = generate_name("ETR", tenant_id=self._tenant_id)
        transfer_doc = {
            "_id": transfer_id,
            "employee": employee,
            "old_department": old_department,
            "new_department": new_department or old_department,
            "old_designation": old_designation,
            "new_designation": new_designation or old_designation,
            "reason": reason,
            "tenant_id": self._tenant_id,
        }
        self._transfer_repo.insert(transfer_doc)

        # 직원 마스터 업데이트
        update_data: dict[str, Any] = {}
        if new_department:
            update_data["department"] = new_department
        if new_designation:
            update_data["designation"] = new_designation

        self._employee_repo.update_by_id(employee, update_data)

        # BR-HR-009: EMPLOYEE_UPDATED 이벤트를 _outbox에 기록 — 급여 동기화 트리거
        outbox_entry = OutboxMixin.create_outbox_entry(
            event_type=EventType.EMPLOYEE_UPDATED,
            doc_id=employee,
            tenant_id=self._tenant_id,
            data={
                "employee_id": employee,
                "department": new_department or old_department,
                "designation": new_designation or old_designation,
                "transfer_id": transfer_id,
            },
        )
        self._employee_repo.update_by_id(employee, {"$push": {"_outbox": outbox_entry}})

        logger.info(
            "인사이동: %s (%s → %s, %s → %s)",
            employee,
            old_department,
            new_department or old_department,
            old_designation,
            new_designation or old_designation,
        )

        return {
            "transfer_id": transfer_id,
            "employee": employee,
            "changes": {
                "department": {"from": old_department, "to": new_department or old_department},
                "designation": {"from": old_designation, "to": new_designation or old_designation},
            },
        }

    def get_transfer_history(
        self,
        employee: str,
    ) -> list[dict[str, Any]]:
        """직원의 인사이동 이력을 조회한다."""
        return self._transfer_repo.find_many(
            {"employee": employee},
            limit=1000,
        )
