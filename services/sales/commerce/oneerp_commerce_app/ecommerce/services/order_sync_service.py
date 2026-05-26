"""마켓플레이스 주문 동기화 서비스 — 채널별 주문을 OneERP로 동기화한다."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_MPO_PREFIX = "MPO"


class OrderSyncService:
    """마켓플레이스 주문 동기화 서비스.

    외부 마켓플레이스에서 수집된 주문을 OneERP 마켓플레이스 주문으로 생성하고
    판매주문으로 자동 전환하는 로직을 제공한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._channel_repo = Repository("ecommerce_channels", tenant_id=tenant_id)
        self._order_repo = Repository("marketplace_orders", tenant_id=tenant_id)

    def sync_orders(
        self,
        channel_id: str,
        external_orders: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """외부 주문 목록을 마켓플레이스 주문으로 동기화한다.

        Args:
            channel_id: 전자상거래 채널 ID
            external_orders: 외부 플랫폼에서 가져온 주문 목록

        Returns:
            동기화 결과 (created, skipped, errors 카운트)

        Raises:
            ValueError: 채널이 존재하지 않거나 비활성인 경우
        """
        channel = self._channel_repo.find_by_id(channel_id)
        if not channel:
            msg = f"채널 '{channel_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if not channel.get("is_active", False):
            msg = f"비활성 채널입니다: {channel_id}"
            raise ValueError(msg)

        created = 0
        skipped = 0
        errors: list[str] = []

        for ext_order in external_orders:
            ext_id = ext_order.get("external_order_id", "")

            # 중복 검사
            existing = self._order_repo.find_many(
                {"channel_id": channel_id, "external_order_id": ext_id},
                limit=1,
            )
            if existing:
                skipped += 1
                continue

            try:
                order_id = generate_name(_MPO_PREFIX, tenant_id=self._tenant_id)
                doc: dict[str, Any] = {
                    "_id": order_id,
                    "tenant_id": self._tenant_id,
                    "channel_id": channel_id,
                    "external_order_id": ext_id,
                    "customer_name": ext_order.get("customer_name", ""),
                    "items": ext_order.get("items", []),
                    "total_amount": str(ext_order.get("total_amount", Decimal(0))),
                    "status": "synced",
                    "synced_at": datetime.now(tz=UTC).isoformat(),
                }
                self._order_repo.insert(doc)
                created += 1
            except Exception as e:
                errors.append(f"{ext_id}: {e}")
                logger.exception("주문 동기화 실패: %s", ext_id)

        logger.info(
            "주문 동기화 완료: channel=%s, created=%d, skipped=%d, errors=%d",
            channel_id,
            created,
            skipped,
            len(errors),
        )

        return {
            "channel_id": channel_id,
            "created": created,
            "skipped": skipped,
            "errors": errors,
        }

    def confirm_order(self, order_id: str) -> dict[str, Any]:
        """마켓플레이스 주문을 확인 상태로 변경한다.

        Args:
            order_id: 마켓플레이스 주문 ID

        Returns:
            업데이트된 주문 정보

        Raises:
            ValueError: 주문이 없거나 확인 불가 상태인 경우
        """
        order = self._order_repo.find_by_id(order_id)
        if not order:
            msg = f"주문 '{order_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if order.get("status") != "synced":
            msg = f"확인 가능한 상태가 아닙니다 (현재: {order.get('status')})"
            raise ValueError(msg)

        self._order_repo.update_by_id(order_id, {"status": "confirmed"})
        logger.info("마켓플레이스 주문 확인: %s", order_id)
        return {"order_id": order_id, "status": "confirmed"}
