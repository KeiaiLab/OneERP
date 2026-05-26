"""마케팅 캠페인 서비스 — 캠페인 발송, 성과 추적, ROI 분석 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-CRM-007: 캠페인 ROI = (revenue - cost) / cost x 100
- BR-CRM-020: 로열티 포인트 적립/차감 (잔액 부족 시 에러)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class CampaignService:
    """마케팅 캠페인 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._email_repo = Repository("email_campaigns", tenant_id=tenant_id)
        self._sms_repo = Repository("sms_campaigns", tenant_id=tenant_id)
        self._list_repo = Repository("marketing_lists", tenant_id=tenant_id)
        self._loyalty_repo = Repository("loyalty_points", tenant_id=tenant_id)

    def create_campaign(
        self,
        campaign_type: str,
        name: str,
        target_list_id: str,
        content: str,
    ) -> dict[str, Any]:
        """캠페인을 생성한다.

        Args:
            campaign_type: "email" 또는 "sms"
            name: 캠페인명
            target_list_id: 대상 마케팅 리스트 ID
            content: 캠페인 내용

        Returns:
            캠페인 생성 결과
        """
        target_list = self._list_repo.find_by_id(target_list_id)
        if not target_list:
            raise_not_found(f"마케팅 리스트 '{target_list_id}'을 찾을 수 없습니다")

        recipient_count = len(target_list.get("members", []))

        repo = self._email_repo if campaign_type == "email" else self._sms_repo
        prefix = "EC" if campaign_type == "email" else "SC"

        campaign_id = generate_name(prefix)
        repo.insert(
            {
                "_id": campaign_id,
                "campaign_name": name,
                "campaign_type": campaign_type,
                "target_list": target_list_id,
                "content": content,
                "recipient_count": recipient_count,
                "status": "draft",
                "sent_count": 0,
                "open_count": 0,
                "click_count": 0,
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "캠페인 생성: %s (유형: %s, 대상: %d명)", campaign_id, campaign_type, recipient_count
        )

        return {
            "campaign_id": campaign_id,
            "campaign_type": campaign_type,
            "recipient_count": recipient_count,
            "status": "draft",
        }

    def calculate_roi(
        self,
        campaign_id: str,
        campaign_type: str = "email",
    ) -> dict[str, Any]:
        """BR-CRM-007: 캠페인 ROI를 계산한다."""
        repo = self._email_repo if campaign_type == "email" else self._sms_repo
        campaign = repo.find_by_id(campaign_id)
        if not campaign:
            raise_not_found(f"캠페인 '{campaign_id}'을 찾을 수 없습니다")

        sent = int(campaign.get("sent_count", 0))
        opened = int(campaign.get("open_count", 0))
        clicked = int(campaign.get("click_count", 0))
        revenue = float(campaign.get("revenue", 0))
        cost = float(campaign.get("cost", 0))

        open_rate = round(opened / sent * 100, 2) if sent > 0 else 0.0
        # BR-CRM-007: 클릭률은 오픈 수 대비 클릭 수로 산출
        click_rate = round(clicked / opened * 100, 2) if opened > 0 else 0.0
        roi = round((revenue - cost) / cost * 100, 2) if cost > 0 else 0.0

        return {
            "campaign_id": campaign_id,
            "sent": sent,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "revenue": revenue,
            "cost": cost,
            "roi": roi,
        }

    # ------------------------------------------------------------------
    # BR-CRM-020: 로열티 포인트 적립/차감
    # ------------------------------------------------------------------

    def award_points(
        self,
        customer_id: str,
        points: int,
        reason: str = "",
    ) -> dict[str, Any]:
        """BR-CRM-020: 로열티 포인트를 적립한다.

        loyalty_points 컬렉션에서 해당 고객의 최신 잔액을 조회하고,
        적립 내역을 기록한 뒤 잔액을 갱신한다.
        """
        if points <= 0:
            raise_unprocessable("ERR-CRM-020", "적립 포인트는 0보다 커야 합니다")

        # 기존 잔액 조회
        existing = self._loyalty_repo.find_many({"customer_id": customer_id}, limit=1)
        current_balance = int(existing[0].get("balance", 0)) if existing else 0
        new_balance = current_balance + points

        record_id = generate_name("LP", tenant_id=self._tenant_id)
        self._loyalty_repo.insert(
            {
                "_id": record_id,
                "customer_id": customer_id,
                "points_earned": points,
                "points_redeemed": 0,
                "balance": new_balance,
                "reason": reason,
                "transaction_type": "earn",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("로열티 적립: 고객=%s, +%d점 → 잔액=%d", customer_id, points, new_balance)
        return {
            "record_id": record_id,
            "customer_id": customer_id,
            "points_earned": points,
            "balance": new_balance,
        }

    def redeem_points(
        self,
        customer_id: str,
        points: int,
    ) -> dict[str, Any]:
        """BR-CRM-020: 로열티 포인트를 차감한다.

        잔액 부족 시 에러를 발생시킨다.
        """
        if points <= 0:
            raise_unprocessable("ERR-CRM-020", "차감 포인트는 0보다 커야 합니다")

        # 기존 잔액 조회
        existing = self._loyalty_repo.find_many({"customer_id": customer_id}, limit=1)
        if not existing:
            raise_unprocessable("ERR-CRM-020", f"고객 '{customer_id}'의 포인트 내역이 없습니다")

        current_balance = int(existing[0].get("balance", 0))
        if current_balance < points:
            raise_unprocessable(
                "ERR-CRM-020",
                f"잔액 부족: 현재 {current_balance}점, 차감 요청 {points}점",
            )

        new_balance = current_balance - points
        record_id = generate_name("LP", tenant_id=self._tenant_id)
        self._loyalty_repo.insert(
            {
                "_id": record_id,
                "customer_id": customer_id,
                "points_earned": 0,
                "points_redeemed": points,
                "balance": new_balance,
                "reason": "포인트 사용",
                "transaction_type": "redeem",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("로열티 차감: 고객=%s, -%d점 → 잔액=%d", customer_id, points, new_balance)
        return {
            "record_id": record_id,
            "customer_id": customer_id,
            "points_redeemed": points,
            "balance": new_balance,
        }
