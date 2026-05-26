"""현장서비스 — 서비스 오더, 방문, 보증클레임 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-CRM-006: 현장서비스 흐름 (서비스주문 open -> 기술자 assigned -> resolved)
- BR-CRM-015: 보증 기간 검증 (purchase_date + warranty_months 기준)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class FieldServiceManager:
    """현장서비스 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._order_repo = Repository("service_orders", tenant_id=tenant_id)
        self._visit_repo = Repository("service_visits", tenant_id=tenant_id)
        self._claim_repo = Repository("warranty_claims", tenant_id=tenant_id)
        self._technician_repo = Repository("service_technicians", tenant_id=tenant_id)
        self._contract_repo = Repository("service_contracts", tenant_id=tenant_id)

    def create_service_order(
        self,
        customer: str,
        issue_description: str,
        priority: str = "medium",
    ) -> dict[str, Any]:
        """서비스 오더를 생성한다."""
        order_id = generate_name("SVO", tenant_id=self._tenant_id)
        self._order_repo.insert(
            {
                "_id": order_id,
                "customer": customer,
                "issue_description": issue_description,
                "priority": priority,
                "status": "open",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("서비스 오더 생성: %s (고객: %s)", order_id, customer)
        return {"order_id": order_id, "status": "open"}

    def assign_technician(
        self,
        order_id: str,
        technician_id: str,
    ) -> dict[str, Any]:
        """기술자를 서비스 오더에 배정한다."""
        order = self._order_repo.find_by_id(order_id)
        if not order:
            raise_not_found(f"서비스 오더 '{order_id}'을 찾을 수 없습니다")

        self._order_repo.update_by_id(
            order_id,
            {
                "technician": technician_id,
                "status": "assigned",
            },
        )

        return {"order_id": order_id, "technician": technician_id, "status": "assigned"}

    def record_visit(
        self,
        order_id: str,
        technician: str,
        resolution: str,
        parts_used: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """서비스 방문을 기록한다."""
        visit_id = generate_name("SVV", tenant_id=self._tenant_id)
        self._visit_repo.insert(
            {
                "_id": visit_id,
                "service_order": order_id,
                "technician": technician,
                "resolution": resolution,
                "parts_used": parts_used or [],
                "status": "completed",
                "tenant_id": self._tenant_id,
            }
        )

        # 서비스 오더 완료 처리
        self._order_repo.update_by_id(order_id, {"status": "resolved"})

        logger.info("서비스 방문 기록: %s (오더: %s)", visit_id, order_id)
        return {"visit_id": visit_id, "order_status": "resolved"}

    def create_warranty_claim(
        self,
        customer: str,
        item_code: str,
        issue: str,
        serial_no: str = "",
    ) -> dict[str, Any]:
        """보증 클레임을 생성한다."""
        claim_id = generate_name("WC", tenant_id=self._tenant_id)
        self._claim_repo.insert(
            {
                "_id": claim_id,
                "customer": customer,
                "item_code": item_code,
                "serial_no": serial_no,
                "issue": issue,
                "status": "open",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("보증 클레임: %s (고객: %s, 아이템: %s)", claim_id, customer, item_code)
        return {"claim_id": claim_id, "status": "open"}

    # ------------------------------------------------------------------
    # BR-CRM-015: 보증 기간 검증
    # ------------------------------------------------------------------

    def check_warranty(
        self,
        item_code: str,
        purchase_date: date,
    ) -> dict[str, Any]:
        """BR-CRM-015: 아이템의 보증 기간을 검증한다.

        service_contracts 컬렉션에서 해당 item_code의 보증 계약을 조회하여
        보증 기간 내인지 확인한다. warranty_months 필드 기준으로 판정한다.
        계약이 없으면 warranty_claims에서 warranty_months를 조회한다.
        """
        # 서비스 계약에서 보증 정보 조회
        contracts = self._contract_repo.find_many(
            {"item_code": item_code, "contract_type": "warranty"},
            limit=1,
        )

        warranty_months: int = 0
        source: str = ""

        if contracts:
            warranty_months = int(contracts[0].get("warranty_months", 12))
            source = "service_contract"
        else:
            # 보증 클레임에서 warranty_months 조회
            claims = self._claim_repo.find_many({"item_code": item_code}, limit=1)
            if claims:
                warranty_months = int(claims[0].get("warranty_months", 12))
                source = "warranty_claim"
            else:
                # 기본 보증 기간 12개월
                warranty_months = 12
                source = "default"

        # 보증 만료일 계산: purchase_date + warranty_months
        warranty_end = purchase_date + timedelta(days=warranty_months * 30)
        today = datetime.now(tz=UTC).date()
        is_under_warranty = today <= warranty_end
        remaining_days = (warranty_end - today).days if is_under_warranty else 0

        logger.info(
            "보증 검증: item=%s, 구매일=%s, 만료일=%s, 유효=%s",
            item_code,
            purchase_date,
            warranty_end,
            is_under_warranty,
        )
        return {
            "item_code": item_code,
            "purchase_date": str(purchase_date),
            "warranty_end": str(warranty_end),
            "warranty_months": warranty_months,
            "is_under_warranty": is_under_warranty,
            "remaining_days": remaining_days,
            "source": source,
        }
