"""Selling 서비스 이벤트 핸들러 — CRM 기회 전환 이벤트 수신 시 견적서 생성.

CRM 서비스가 OPPORTUNITY_CONVERTED 이벤트를 발행하면,
selling 서비스가 자체 Quotation 모델에 맞춰 견적서를 생성한다.

L2 비즈니스 룰 매핑:
- BR-SELL-015: CRM 기회 -> 견적 자동 전환 (OPPORTUNITY_CONVERTED 이벤트)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_selling_app.models.quotation import Quotation, QuotationItem

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()


@event_registry.on(
    EventType.OPPORTUNITY_CONVERTED,
    description="기회 전환 → 견적서 생성",
)
async def handle_opportunity_converted(payload: dict[str, Any], event_id: str) -> None:
    """CRM 기회 전환 이벤트를 수신하여 견적서를 생성한다.

    selling 서비스 내부에서 Quotation 모델 스키마를 준수하여 생성하므로
    크로스서비스 DB 직접 쓰기가 발생하지 않는다.
    """
    tenant_id, _doc_id = extract_tenant_and_doc(payload)
    event_data = payload.get("event", {}).get("data", {})

    opportunity_id = event_data.get("opportunity_id", "")
    customer_id = event_data.get("customer_id", "")
    raw_items = event_data.get("items", [])
    valid_till_str = event_data.get("valid_till")

    # 이벤트 아이템을 QuotationItem으로 변환
    quotation_items: list[QuotationItem] = []
    for idx, item in enumerate(raw_items, start=1):
        qty = Decimal(str(item.get("qty", 0) or 0))
        rate = Decimal(str(item.get("rate", 0) or 0))
        quotation_items.append(
            QuotationItem(
                idx=idx,
                item_code=item.get("item_code", item.get("item", "")),
                item_name=item.get("item_name", item.get("item", "")),
                qty=qty,
                rate=rate,
                amount=qty * rate,
            )
        )

    total = sum((i.amount for i in quotation_items), Decimal(0))
    valid_till = date.fromisoformat(valid_till_str) if valid_till_str else None

    quot_id = generate_name("QTN", tenant_id=tenant_id)
    quotation = Quotation(
        _id=quot_id,
        tenant_id=tenant_id,
        customer_id=customer_id,
        transaction_date=datetime.now(tz=UTC).date(),
        valid_till=valid_till,
        items=quotation_items,
        total=total,
        grand_total=total,
    )

    quot_repo = Repository("quotations", tenant_id=tenant_id)
    quot_repo.insert(quotation)

    logger.info(
        "기회 전환 견적서 생성 완료: opportunity=%s, quotation=%s, event_id=%s",
        opportunity_id,
        quot_id,
        event_id,
    )
