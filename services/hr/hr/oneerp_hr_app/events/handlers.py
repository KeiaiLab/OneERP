"""HR 이벤트 핸들러 — 채용/퇴사/발령/조직개편/직급변경/급여완료/휴가승인.

Spec III Wave C-2 선행 정합 단계로, 현재는 각 핸들러가 placeholder(no-op)이며
이후 Spec III gate 셀이 도메인 로직을 채운다. 시그니처는 core 표준
`async (payload: dict, event_id: str) -> None` 을 따르며 accounting 패턴을 미러한다.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from oneerp_core.events.schemas import EventType

if TYPE_CHECKING:
    from oneerp_core.events.handler_registry import EventHandlerRegistry

logger = logging.getLogger(__name__)


async def on_employee_hired(payload: dict[str, Any], event_id: str) -> None:
    """직원 채용 이벤트 — 온보딩 체크리스트 생성 훅 (Spec III 예정)."""
    logger.debug("employee.hired 수신", extra={"event_id": event_id, "payload": payload})


async def on_employee_terminated(payload: dict[str, Any], event_id: str) -> None:
    """직원 퇴사 이벤트 — 오프보딩/정산 트리거 훅 (Spec III 예정)."""
    logger.debug("employee.terminated 수신", extra={"event_id": event_id, "payload": payload})


async def on_employee_transferred(payload: dict[str, Any], event_id: str) -> None:
    """직원 발령 이벤트 — 조직/보고라인 갱신 훅 (Spec III 예정)."""
    logger.debug("employee.transferred 수신", extra={"event_id": event_id, "payload": payload})


async def on_department_reorganized(payload: dict[str, Any], event_id: str) -> None:
    """부서 개편 이벤트 — 조직도 재계산 훅 (Spec III 예정)."""
    logger.debug("department.reorganized 수신", extra={"event_id": event_id, "payload": payload})


async def on_designation_changed(payload: dict[str, Any], event_id: str) -> None:
    """직급 변경 이벤트 — 급여/결재권 재매핑 훅 (Spec III 예정)."""
    logger.debug("designation.changed 수신", extra={"event_id": event_id, "payload": payload})


async def on_payroll_run_completed(payload: dict[str, Any], event_id: str) -> None:
    """급여 처리 완료 이벤트 — 명세서 알림/회계 연동 훅 (Spec III 예정)."""
    logger.debug("payroll.run.completed 수신", extra={"event_id": event_id, "payload": payload})


async def on_leave_approved(payload: dict[str, Any], event_id: str) -> None:
    """휴가 승인 이벤트 — 잔액 차감/근태 동기화 훅 (Spec III 예정)."""
    logger.debug(
        "leave_application.approved 수신",
        extra={"event_id": event_id, "payload": payload},
    )


def register_handlers(registry: EventHandlerRegistry) -> None:
    """주어진 registry 에 HR 도메인 7개 핸들러를 등록한다.

    accounting 은 모듈 import 시점에 @event_registry.on 데코레이터로 등록하지만,
    hr 는 FastAPI 기동 시점 명시 호출 패턴(플랜 §C2-2)을 택한다. 양쪽 모두
    최종 구독 결과는 동일하다.
    """
    registry.register_handler(
        EventType.EMPLOYEE_HIRED, on_employee_hired, description="직원 채용 후속 처리"
    )
    registry.register_handler(
        EventType.EMPLOYEE_TERMINATED,
        on_employee_terminated,
        description="직원 퇴사 후속 처리",
    )
    registry.register_handler(
        EventType.EMPLOYEE_TRANSFERRED,
        on_employee_transferred,
        description="직원 발령 후속 처리",
    )
    registry.register_handler(
        EventType.DEPARTMENT_REORGANIZED,
        on_department_reorganized,
        description="부서 개편 후속 처리",
    )
    registry.register_handler(
        EventType.DESIGNATION_CHANGED,
        on_designation_changed,
        description="직급 변경 후속 처리",
    )
    registry.register_handler(
        EventType.PAYROLL_RUN_COMPLETED,
        on_payroll_run_completed,
        description="급여 완료 후속 처리",
    )
    registry.register_handler(
        EventType.LEAVE_APPLICATION_APPROVED,
        on_leave_approved,
        description="휴가 승인 후속 처리",
    )
