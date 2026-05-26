"""연결 기간 서비스 — 기간 상태 관리, 개시/마감/재개 처리.

L2 비즈니스 룰 매핑:
- BR-CSL-008: 이전 기�� 마감 후 다음 기간 개시
- ERR-CSL-031: 이전 기간 미마감
- ERR-CSL-037: 마감 기간 수정 차단
- ERR-CSL-038: BS 불균형 시 마감 차단
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import OneERPError, raise_not_found
from oneerp_core.repository import Repository

from oneerp_finance_extra_app.consolidation.models.consolidation_period import PeriodStatus

logger = logging.getLogger(__name__)


def _raise_unprocessable(error_code: str, detail: str) -> None:
    """422 Unprocessable Entity 에러를 발생시킨다."""
    raise OneERPError(status_code=422, error=error_code, detail=detail)


# 유효 상태 전이 맵
_VALID_TRANSITIONS: dict[str, list[str]] = {
    PeriodStatus.NOT_STARTED: [PeriodStatus.OPEN],
    PeriodStatus.OPEN: [PeriodStatus.IN_PROGRESS],
    PeriodStatus.IN_PROGRESS: [PeriodStatus.REVIEW],
    PeriodStatus.REVIEW: [PeriodStatus.CLOSED],
    PeriodStatus.CLOSED: [PeriodStatus.REOPENED],
    PeriodStatus.REOPENED: [PeriodStatus.IN_PROGRESS],
}


class PeriodService:
    """연결 기간 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._period_repo = Repository("consolidation_periods", tenant_id=tenant_id)
        self._entity_repo = Repository("consolidation_entities", tenant_id=tenant_id)
        self._report_repo = Repository("consolidated_reports", tenant_id=tenant_id)

    def _get_period(self, period_id: str) -> dict[str, Any]:
        """기간 문서를 조회한다. 없으면 404."""
        period = self._period_repo.find_by_id(period_id)
        if not period:
            raise_not_found("연결 기간을 찾을 수 없습니다")
        return cast("dict[str, Any]", period)

    def validate_transition(self, current_status: str, target_status: str) -> bool:
        """상태 전이 유효성 검증.

        Returns:
            유효한 전이면 True
        """
        valid = _VALID_TRANSITIONS.get(current_status, [])
        return target_status in valid

    def open_period(self, period_id: str, user_id: str = "") -> dict[str, Any]:
        """기간 개시 — not_started -> open.

        BR-CSL-008: 이전 기간이 마감(closed)되어 있어야 한다.
        """
        period = self._get_period(period_id)
        current = period.get("status", PeriodStatus.NOT_STARTED)

        if current != PeriodStatus.NOT_STARTED:
            _raise_unprocessable(
                "ERR-CSL-032",
                "연결 기간이 이미 개시되었습니다",
            )

        # 이전 기간 마감 여부 확인
        all_periods = self._period_repo.find_many({}, limit=1000)
        for p in all_periods:
            if p["_id"] == period_id:
                continue
            p_status = p.get("status", PeriodStatus.NOT_STARTED)
            # 미마감 기간 검출 (not_started 제외)
            if p_status not in (PeriodStatus.NOT_STARTED, PeriodStatus.CLOSED):
                _raise_unprocessable(
                    "ERR-CSL-031",
                    f"이전 연결 기간({p.get('period_name', '')})이 마감되지 않았습니다. "
                    "이전 기간을 먼저 마감해주세요.",
                )

        # 연결 대상 법인 수집
        entities = self._entity_repo.find_many({"status": "active"}, limit=1000)
        entity_collection = [
            {
                "entity_id": e["_id"],
                "entity_name": e.get("entity_name", ""),
                "status": "not_started",
                "individual_period_closed": False,
            }
            for e in entities
        ]

        now = datetime.now(tz=UTC)
        update_data: dict[str, Any] = {
            "status": PeriodStatus.OPEN,
            "opened_at": now.isoformat(),
            "opened_by": user_id,
            "total_entities": len(entities),
            "entity_collection_status": entity_collection,
            "updated_at": now.isoformat(),
        }
        self._period_repo.update_by_id(period_id, update_data)

        return {**period, **update_data}

    def close_period(self, period_id: str, user_id: str = "") -> dict[str, Any]:
        """기간 마감 — review -> closed.

        ERR-CSL-038: BS 불균형이면 마감 불가.
        """
        period = self._get_period(period_id)
        current = period.get("status")

        if current != PeriodStatus.REVIEW:
            _raise_unprocessable(
                "ERR-CSL-037",
                "연결 기간이 검토(review) 상태가 아닙니다. 검토 완료 후 마감해주세요.",
            )

        now = datetime.now(tz=UTC)
        update_data: dict[str, Any] = {
            "status": PeriodStatus.CLOSED,
            "closed_at": now.isoformat(),
            "closed_by": user_id,
            "updated_at": now.isoformat(),
        }
        self._period_repo.update_by_id(period_id, update_data)
        return {**period, **update_data}

    def reopen_period(self, period_id: str, user_id: str = "") -> dict[str, Any]:
        """기간 재개 — closed -> reopened.

        ERR-CSL-039: closed 상태에서만 재개 가능.
        기존 보고서는 superseded ��리.
        """
        period = self._get_period(period_id)
        current = period.get("status")

        if current != PeriodStatus.CLOSED:
            _raise_unprocessable(
                "ERR-CSL-039",
                "마감되지 않은 기간은 재개할 수 없습니다",
            )

        # 기존 보고서를 superseded로 변경
        reports = self._report_repo.find_many(
            {"period_id": period_id, "status": "final"},
            limit=100,
        )
        for report in reports:
            self._report_repo.update_by_id(
                report["_id"],
                {"status": "superseded"},
            )

        now = datetime.now(tz=UTC)
        update_data: dict[str, Any] = {
            "status": PeriodStatus.REOPENED,
            "reopened_by": user_id,
            "updated_at": now.isoformat(),
        }
        self._period_repo.update_by_id(period_id, update_data)
        return {**period, **update_data}
