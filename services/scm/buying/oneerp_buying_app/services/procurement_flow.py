"""구매 프로세스 자동화 서비스.

자재요청 제출 -> 구매주문 초안 자동 생성.

L2 비즈니스 룰 매핑:
- BR-BUY-001: MR -> PO 자동 전환 (request_type=purchase만 대상)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_buying_app.models.purchase_order import PurchaseOrder, PurchaseOrderItem

logger = logging.getLogger(__name__)


def _normalize_date(value: object) -> date:
    """문서/문자열 날짜 값을 date 객체로 정규화한다."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value:
        return date.fromisoformat(str(value))
    return datetime.now(tz=UTC).date()


class ProcurementFlowService:
    """구매 프로세스 자동화 서비스.

    자재요청 제출 → 구매주문 초안 자동 생성.
    """

    def handle_material_request_submitted(self, event_data: dict, tenant_id: str) -> str | None:
        """BR-BUY-001: 자재요청 제출 이벤트를 처리하여 구매주문 초안을 생성한다.

        event_data에서 자재요청 doc_id를 추출하고,
        자재요청 문서를 조회하여 구매주문 초안을 생성한다.

        Returns: 생성된 PurchaseOrder doc_id, 실패 시 None
        """
        doc_id = event_data.get("doc_id")
        if not doc_id:
            logger.warning("이벤트 데이터에 doc_id가 누락되었습니다: %s", event_data)
            return None

        mr_repo = Repository("material_requests", tenant_id=tenant_id)
        mr_doc = mr_repo.find_by_id(doc_id)
        if not mr_doc:
            logger.warning("자재요청 문서를 찾을 수 없습니다: %s", doc_id)
            return None

        # 자재요청이 purchase 유형이 아니면 구매주문을 생성하지 않는다
        if mr_doc.get("request_type", "purchase") != "purchase":
            logger.info(
                "구매 유형이 아닌 자재요청은 건너뜁니다: %s (유형: %s)",
                doc_id,
                mr_doc.get("request_type"),
            )
            return None

        transaction_date = datetime.now(tz=UTC).date()
        delivery_date = _normalize_date(mr_doc.get("required_date"))

        # 구매주문 아이템 매핑
        po_items = []
        for idx, item in enumerate(mr_doc.get("items", []), start=1):
            po_items.append(
                PurchaseOrderItem(
                    idx=idx,
                    item_code=item.get("item_code", ""),
                    item_name=item.get("item_name", ""),
                    qty=item.get("qty", 0),
                    rate=Decimal(0),  # 단가는 이후 공급업체 견적에서 결정
                    amount=Decimal(0),
                    received_qty=Decimal(0),
                    delivery_date=delivery_date,
                )
            )

        po_id = generate_name("PO", tenant_id=tenant_id)
        po_doc = PurchaseOrder(
            _id=po_id,
            tenant_id=tenant_id,
            supplier_id="",
            supplier_name="",
            transaction_date=transaction_date,
            items=po_items,
            total=Decimal(0),
            grand_total=Decimal(0),
        )

        po_repo = Repository("purchase_orders", tenant_id=tenant_id)
        po_repo.insert(po_doc)

        logger.info(
            "구매주문 초안 생성 완료: %s (자재요청: %s, 아이템 %d건)",
            po_id,
            doc_id,
            len(po_items),
        )
        return po_id
