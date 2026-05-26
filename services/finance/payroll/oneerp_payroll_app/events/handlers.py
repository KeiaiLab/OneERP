"""Payroll 서비스 이벤트 핸들러.

- 급여처리 제출 -> 급여 계산 실행
- 직원 정보 변경 -> DRAFT 급여대장의 직원 스냅샷 동기화

L2 비즈니스 룰 매핑:
- BR-PAY-014: HR 직원 동기화 (EMPLOYEE_UPDATED -> Draft만 갱신)
- BR-PAY-015: PayrollEntry 제출 시 PAYROLL_ENTRY_SUBMITTED 이벤트 발행

app_factory._build_event_lifespan에서 핸들러를 호출할 때
시그니처는 (data: dict, event_id: str) 형태이다.
data는 EventEnvelope JSON 전체이며, tenant_id는 data["event"]["tenant_id"]에서 추출한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()

# EMPLOYEE_UPDATED 이벤트 수신 시 동기화할 필드 목록
_EMPLOYEE_SYNC_FIELDS = ("employee_name", "department", "designation")


@event_registry.on(EventType.PAYROLL_ENTRY_SUBMITTED, description="급여처리 제출 → 급여 계산 실행")
async def handle_payroll_entry_submitted(data: dict[str, Any], event_id: str) -> None:
    """급여처리 제출 시 직원별 급여를 계산한다."""
    from oneerp_payroll_app.services.payroll_calculation_service import PayrollCalculationService

    tenant_id, doc_id = extract_tenant_and_doc(data)
    svc = PayrollCalculationService(tenant_id)
    slip_ids = svc.process_payroll(doc_id)
    logger.info(
        "급여 계산 완료: doc_id=%s → %d명, event_id=%s",
        doc_id,
        len(slip_ids),
        event_id,
    )


@event_registry.on(
    EventType.EMPLOYEE_UPDATED,
    description="직원 정보 변경 → DRAFT 급여대장 직원 스냅샷 동기화",
)
async def handle_employee_updated(data: dict[str, Any], event_id: str) -> None:
    """HR 직원 정보 변경 시 미완료(DRAFT) 급여대장의 직원 스냅샷을 갱신한다.

    SUBMITTED/CANCELLED 상태의 급여대장은 확정 이력이므로 수정하지 않는다.
    """
    tenant_id, employee_id = extract_tenant_and_doc(data)
    event_data: dict[str, Any] = data.get("event", {}).get("data", {})

    # 동기화할 변경 필드만 추출
    updates: dict[str, Any] = {k: v for k, v in event_data.items() if k in _EMPLOYEE_SYNC_FIELDS}
    if not updates:
        logger.debug(
            "동기화 대상 필드 없음: employee_id=%s, event_id=%s",
            employee_id,
            event_id,
        )
        return

    repo = Repository("payroll_entries", tenant_id=tenant_id)

    # DRAFT 상태이면서 해당 직원을 포함하는 급여대장 조회
    draft_entries = repo.find_many(
        {
            "docstatus": DocStatus.DRAFT,
            "employees.employee_id": employee_id,
        },
        limit=0,
    )

    updated_count = 0
    for entry in draft_entries:
        employees: list[dict[str, Any]] = entry.get("employees", [])
        changed = False
        for emp in employees:
            if emp.get("employee_id") != employee_id:
                continue
            for field_name, new_value in updates.items():
                if emp.get(field_name) != new_value:
                    emp[field_name] = new_value
                    changed = True

        if changed:
            repo.update_by_id(entry["_id"], {"employees": employees})
            updated_count += 1

    logger.info(
        "직원 스냅샷 동기화 완료: employee_id=%s, 갱신 %d건, event_id=%s",
        employee_id,
        updated_count,
        event_id,
    )
