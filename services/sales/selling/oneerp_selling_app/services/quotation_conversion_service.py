"""견적서→판매주문 전환 서비스.

L2 비즈니스 룰 매핑:
- BR-SELL-001: 견적→주문 전환 조건 (docstatus=submitted, converted_to=null)
- BR-SELL-002: 견적 부분 전환 (item_indices로 품목 선택)
- BR-SELL-017: 견적 유효기한 경과 시 경고만 (전환은 허용)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_selling_app.services.sales_partner_snapshot import resolve_sales_partner_snapshot

logger = logging.getLogger(__name__)

_SO_PREFIX = "SO"


class QuotationConversionService:
    """견적서를 판매주문으로 전환하는 비즈니스 로직.

    FL1(Order-to-Cash) 및 FL6(CRM-to-Selling) 흐름의 전제조건.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._qtn_repo = Repository("quotations", tenant_id=tenant_id)
        self._so_repo = Repository("sales_orders", tenant_id=tenant_id)

    def convert_to_sales_order(
        self,
        quotation_id: str,
        item_indices: list[int] | None = None,
    ) -> dict[str, Any]:
        """BR-SELL-001/002: 견적서를 판매주문으로 전환한다.

        BR-SELL-001: docstatus=submitted이고 converted_to=null인 경우만 전환 가능.
        BR-SELL-002: item_indices 제공 시 지정 품목만 전환, 미제공 시 전체.
        BR-SELL-017: 유효기한 경과 시 경고 로그만 남기고 전환 허용.

        Args:
            quotation_id: 전환 대상 견적서 ID
            item_indices: 전환할 아이템 인덱스 목록 (None이면 전체)

        Returns:
            생성된 판매주문 정보 (so_id, source_quotation, items)

        Raises:
            OneERPError(ERR-SELL-030): 미제출 상태
            OneERPError(ERR-SELL-025): 이미 전환됨
        """
        quotation = self._qtn_repo.find_by_id(quotation_id)
        if not quotation:
            raise_not_found(f"견적서 '{quotation_id}'를 찾을 수 없습니다")
        quotation = cast("dict[str, Any]", quotation)

        # 제출 상태 검증
        if quotation.get("docstatus") != "submitted":
            raise_unprocessable(
                "ERR-SELL-030",
                "제출된 견적서만 판매주문으로 전환할 수 있습니다",
            )

        # 중복 전환 방지
        if quotation.get("converted_to"):
            raise_unprocessable(
                "ERR-SELL-025",
                f"이미 전환된 견적서입니다 (SO: {quotation['converted_to']})",
            )

        # BR-SELL-017: 유효기한 경과 확인 (경고만, 전환은 허용)
        valid_till = quotation.get("valid_till")
        if valid_till:
            from datetime import date as _date

            if isinstance(valid_till, str):
                valid_till = _date.fromisoformat(valid_till[:10])
            today = datetime.now(UTC).date()
            if valid_till < today:
                logger.warning(
                    "견적서 유효기한 경과: %s (유효기한: %s, 오늘: %s)",
                    quotation_id,
                    valid_till,
                    today,
                )

        # BR-SELL-002: 전환할 아이템 선택
        all_items: list[dict[str, Any]] = quotation.get("items", [])
        if item_indices is not None:
            # 유효 범위(0 ~ len-1) 밖 인덱스가 있으면 즉시 거부
            invalid_indices = [i for i in item_indices if i < 0 or i >= len(all_items)]
            if invalid_indices:
                raise_unprocessable(
                    "ERR-SELL-032",
                    f"유효하지 않은 아이템 인덱스: {invalid_indices}",
                )
            items = [all_items[i] for i in item_indices]
        else:
            items = list(all_items)

        # 판매주문 생성
        so_id = generate_name(_SO_PREFIX, tenant_id=self._tenant_id)
        so_doc: dict[str, Any] = {
            "_id": so_id,
            "tenant_id": self._tenant_id,
            "customer_id": quotation.get("customer_id", ""),
            "customer_name": quotation.get("customer_name", ""),
            **resolve_sales_partner_snapshot(self._tenant_id, quotation.get("customer_id")),
            "items": items,
            "source_quotation": quotation_id,
            "docstatus": "draft",
            "transaction_date": datetime.now(UTC).date().isoformat(),
        }
        self._so_repo.insert(so_doc)

        # 원본 견적서에 전환 정보 기록
        self._qtn_repo.update_by_id(
            quotation_id,
            {
                "converted_to": so_id,
                "conversion_date": datetime.now(UTC).isoformat(),
            },
        )

        logger.info("견적서 전환 완료: %s → %s", quotation_id, so_id)

        return {
            "so_id": so_id,
            "source_quotation": quotation_id,
            "items": items,
        }
