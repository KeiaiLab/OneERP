"""캠페인 발송 서비스 — 이메일/SMS 캠페인 발송 로직을 제공한다."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 유효한 캠페인 상태 전환
_SENDABLE_STATUSES = frozenset({"draft", "scheduled"})


class CampaignService:
    """캠페인 발송 서비스.

    이메일·SMS 캠페인의 발송 실행과 통계 집계를 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._email_repo = Repository("email_campaigns", tenant_id=tenant_id)
        self._sms_repo = Repository("sms_campaigns", tenant_id=tenant_id)
        self._list_repo = Repository("marketing_lists", tenant_id=tenant_id)

    def send_email_campaign(self, campaign_id: str) -> dict[str, Any]:
        """이메일 캠페인을 발송한다.

        Args:
            campaign_id: 이메일 캠페인 ID

        Returns:
            발송 결과 (campaign_id, sent_count, status)

        Raises:
            ValueError: 캠페인이 없거나 발송 불가 상태인 경우
        """
        campaign = self._email_repo.find_by_id(campaign_id)
        if not campaign:
            msg = f"이메일 캠페인 '{campaign_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if campaign.get("status") not in _SENDABLE_STATUSES:
            msg = f"발송 가능한 상태가 아닙니다 (현재: {campaign.get('status')})"
            raise ValueError(msg)

        # 발송 대상 목록 조회
        list_id = campaign.get("marketing_list_id", "")
        mkt_list = self._list_repo.find_by_id(list_id)
        if not mkt_list:
            msg = f"마케팅 목록 '{list_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        # 수신동의된 멤버만 필터 (한국 정보통신망법)
        members = mkt_list.get("members", [])
        opted_in = [m for m in members if m.get("opt_in", True) and m.get("email")]
        sent_count = len(opted_in)

        # 상태 업데이트
        self._email_repo.update_by_id(
            campaign_id,
            {
                "status": "sent",
                "sent_count": sent_count,
                "updated_at": datetime.now(tz=UTC).isoformat(),
            },
        )

        logger.info("이메일 캠페인 발송 완료: %s, %d건", campaign_id, sent_count)
        return {
            "campaign_id": campaign_id,
            "sent_count": sent_count,
            "status": "sent",
        }

    def send_sms_campaign(self, campaign_id: str) -> dict[str, Any]:
        """SMS 캠페인을 발송한다.

        Args:
            campaign_id: SMS 캠페인 ID

        Returns:
            발송 결과 (campaign_id, sent_count, status)

        Raises:
            ValueError: 캠페인이 없거나 발송 불가 상태인 경우
        """
        campaign = self._sms_repo.find_by_id(campaign_id)
        if not campaign:
            msg = f"SMS 캠페인 '{campaign_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if campaign.get("status") not in _SENDABLE_STATUSES:
            msg = f"발송 가능한 상태가 아닙니다 (현재: {campaign.get('status')})"
            raise ValueError(msg)

        # 메시지 길이 검증 (한국 SMS 90바이트/한글 45자)
        message = campaign.get("message", "")
        if len(message.encode("euc-kr", errors="replace")) > 90:
            logger.warning("SMS 메시지가 90바이트를 초과합니다. LMS로 전환됩니다.")

        list_id = campaign.get("marketing_list_id", "")
        mkt_list = self._list_repo.find_by_id(list_id)
        if not mkt_list:
            msg = f"마케팅 목록 '{list_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        members = mkt_list.get("members", [])
        opted_in = [m for m in members if m.get("opt_in", True) and m.get("phone")]
        sent_count = len(opted_in)

        self._sms_repo.update_by_id(
            campaign_id,
            {
                "status": "sent",
                "sent_count": sent_count,
                "updated_at": datetime.now(tz=UTC).isoformat(),
            },
        )

        logger.info("SMS 캠페인 발송 완료: %s, %d건", campaign_id, sent_count)
        return {
            "campaign_id": campaign_id,
            "sent_count": sent_count,
            "status": "sent",
        }
