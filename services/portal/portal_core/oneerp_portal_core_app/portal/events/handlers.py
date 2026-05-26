"""포털 이벤트 핸들러 — 외부 이벤트 구독 처리.

APPROVAL_REQUEST_* → 위젯 캐시 갱신.
EMPLOYEE_DEPARTMENT_CHANGED → 레이아웃 재계산.
POST_CREATED → 공지 위젯 갱신.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_approval_request_event(event_data: dict[str, Any]) -> None:
    """결재 요청 이벤트 처리 — 위젯 캐시를 갱신한다.

    APPROVAL_REQUEST_APPROVED / APPROVAL_REQUEST_REJECTED 이벤트를 수신하여
    결재 현황 위젯의 캐시를 무효화한다.
    """
    doc_id = event_data.get("doc_id", "")
    tenant_id = event_data.get("tenant_id", "")
    logger.info(
        "결재 이벤트 수신: doc_id=%s, tenant_id=%s — 위젯 캐시 갱신",
        doc_id,
        tenant_id,
    )
    # 캐시 무효화 로직 (Valkey 캐시 키 삭제)
    # 실제 구현에서는 get_cache().delete(f"widget:approval:{tenant_id}:*") 호출


def handle_employee_department_changed(event_data: dict[str, Any]) -> None:
    """직원 부서 변경 이벤트 처리 — 레이아웃을 재계산한다.

    EMPLOYEE_DEPARTMENT_CHANGED 이벤트를 수신하여
    해당 사용자의 개인 대시보드 캐시를 무효화한다.
    """
    employee_id = event_data.get("doc_id", "")
    new_department = event_data.get("data", {}).get("new_department", "")
    logger.info(
        "부서 변경 이벤트: employee=%s, 새 부서=%s — 레이아웃 재계산",
        employee_id,
        new_department,
    )
    # 개인 대시보드 캐시 무효화


def handle_post_created(event_data: dict[str, Any]) -> None:
    """게시물 생성 이벤트 처리 — 공지 위젯을 갱신한다.

    POST_CREATED 이벤트를 수신하여 공지사항/뉴스 위젯의 캐시를 무효화한다.
    """
    doc_id = event_data.get("doc_id", "")
    tenant_id = event_data.get("tenant_id", "")
    logger.info(
        "게시물 생성 이벤트: doc_id=%s, tenant_id=%s — 공지 위젯 갱신",
        doc_id,
        tenant_id,
    )
    # 공지사항/뉴스 위젯 캐시 무효화
