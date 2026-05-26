"""Accounting 이벤트 핸들러 — 도메인 이벤트 수신 시 자동 분개 생성.

매출전표, 매입전표, 수금/지급, 경비 청구, 급여 제출 이벤트를 구독하여
JournalAutoService를 통해 복식부기 분개를 자동 생성한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc

from oneerp_accounting_app.services.journal_auto_service import JournalAutoService

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()


@event_registry.on(EventType.SALES_INVOICE_SUBMITTED, description="매출전표 자동 분개 생성")
async def handle_sales_invoice_submitted(payload: dict[str, Any], event_id: str) -> None:
    """매출전표 제출 이벤트 → 매출 분개 자동 생성.

    이벤트 데이터에 핵심 필드가 포함된 경우 크로스서비스 조회 없이 처리한다.
    """
    tenant_id, doc_id = extract_tenant_and_doc(payload)
    event_data = payload.get("event", {}).get("data", {}) or payload.get("data", {})

    svc = JournalAutoService(tenant_id)
    # 이벤트 데이터에 grand_total이 있으면 크로스서비스 조회 없이 처리
    if event_data.get("grand_total"):
        je_id = svc.create_sales_invoice_journal_from_event(event_data)
    else:
        je_id = svc.create_sales_invoice_journal(doc_id)
    logger.info(
        "매출전표 자동 분개 완료: doc_id=%s, je_id=%s, event_id=%s",
        doc_id,
        je_id,
        event_id,
    )


@event_registry.on(EventType.PURCHASE_INVOICE_SUBMITTED, description="매입전표 자동 분개 생성")
async def handle_purchase_invoice_submitted(payload: dict[str, Any], event_id: str) -> None:
    """매입전표 제출 이벤트 → 매입 분개 자동 생성.

    이벤트 데이터에 핵심 필드가 포함된 경우 크로스서비스 조회 없이 처리한다.
    """
    tenant_id, doc_id = extract_tenant_and_doc(payload)
    event_data = payload.get("event", {}).get("data", {}) or payload.get("data", {})

    svc = JournalAutoService(tenant_id)
    if event_data.get("grand_total"):
        je_id = svc.create_purchase_invoice_journal_from_event(event_data)
    else:
        je_id = svc.create_purchase_invoice_journal(doc_id)
    logger.info(
        "매입전표 자동 분개 완료: doc_id=%s, je_id=%s, event_id=%s",
        doc_id,
        je_id,
        event_id,
    )


@event_registry.on(EventType.PAYMENT_ENTRY_SUBMITTED, description="수금/지급 자동 분개 생성")
async def handle_payment_entry_submitted(payload: dict[str, Any], event_id: str) -> None:
    """수금/지급 전표 제출 이벤트 → 수금/지급 분개 자동 생성."""
    tenant_id, doc_id = extract_tenant_and_doc(payload)

    svc = JournalAutoService(tenant_id)
    je_id = svc.create_payment_journal(doc_id)
    logger.info(
        "수금/지급 자동 분개 완료: doc_id=%s, je_id=%s, event_id=%s",
        doc_id,
        je_id,
        event_id,
    )


@event_registry.on(EventType.EXPENSE_CLAIM_APPROVED, description="경비 청구 자동 분개 생성")
async def handle_expense_claim_approved(payload: dict[str, Any], event_id: str) -> None:
    """경비 청구 승인 이벤트 → 경비 분개 자동 생성.

    이벤트 데이터(expenses 서비스가 발행)에서 직접 분개를 생성한다.
    크로스서비스 DB 조회 없이 이벤트 페이로드만 사용한다.
    """
    tenant_id, doc_id = extract_tenant_and_doc(payload)
    event_data = payload.get("event", {}).get("data", {}) or payload.get("data", {})
    # 이벤트 페이로드에 doc_id가 없으면 봉투에서 주입
    event_data.setdefault("doc_id", doc_id)

    svc = JournalAutoService(tenant_id)
    je_id = svc.create_expense_claim_journal_from_event(event_data)
    logger.info(
        "경비 청구 자동 분개 완료: doc_id=%s, je_id=%s, event_id=%s",
        doc_id,
        je_id,
        event_id,
    )


@event_registry.on(EventType.PAYROLL_ENTRY_SUBMITTED, description="급여 자동 분개 생성")
async def handle_payroll_entry_submitted(payload: dict[str, Any], event_id: str) -> None:
    """급여 제출 이벤트 → 급여 분개 자동 생성.

    payroll 서비스가 급여명세 합산 데이터를 이벤트에 포함하여 발행한다.
    크로스서비스 DB 조회 없이 이벤트 페이로드만 사용한다.
    """
    tenant_id, doc_id = extract_tenant_and_doc(payload)
    event_data = payload.get("event", {}).get("data", {}) or payload.get("data", {})
    # 이벤트 페이로드에 doc_id가 없으면 봉투에서 주입
    event_data.setdefault("doc_id", doc_id)

    svc = JournalAutoService(tenant_id)
    je_id = svc.create_payroll_journal_from_event(event_data)
    logger.info(
        "급여 자동 분개 완료: doc_id=%s, je_id=%s, event_id=%s",
        doc_id,
        je_id,
        event_id,
    )
