"""업무보고 리마인더(미제출자 식별·트리거 평가) 서비스.

L2 사양: docs/product/scope/modules/work-report/L2-spec.md
- 계산 로직 4.5: 미제출자 식별
- BR-WRP-012: 리마인더 최대 알림 횟수 제한

설계 주석:
- DB I/O는 상위 라우터가 담당. 본 서비스는 입력 DTO/집합 기반 pure 로직만 수행
- 트리거 시점 계산은 표준 라이브러리 datetime.time 산술만 사용 (LLM 호출 금지)
- 중복 발송 방지는 ReminderLog.sent_count를 외부에서 주입 받아 판정
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, time, timedelta
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ReminderTrigger(StrEnum):
    """리마인더 트리거 유형."""

    BEFORE_DEADLINE = "before_deadline"
    AFTER_DEADLINE = "after_deadline"
    FIXED_TIME = "fixed_time"


@dataclass(frozen=True)
class ReminderPolicy:
    """ReportReminder 정책 (엔티티 1.4 핵심 필드만 투영)."""

    trigger_type: ReminderTrigger
    trigger_offset_hours: int
    deadline_time: time
    trigger_time: time | None
    max_reminders: int


class ReminderIdentificationService:
    """미제출자 식별·리마인더 트리거 평가."""

    # ------------------------------------------------------------------
    # 4.5 미제출자 식별
    # ------------------------------------------------------------------

    def identify_missing_submissions(
        self,
        *,
        target_employees: list[dict[str, Any]],
        submitted_author_ids: set[str],
        sent_counts: dict[str, int],
        max_reminders: int,
    ) -> list[dict[str, Any]]:
        """대상자 중 미제출 + 알림 가능한 직원 목록을 반환한다.

        BR-WRP-012: sent_count >= max_reminders 인 직원은 제외.
        """
        recipients: list[dict[str, Any]] = []
        for employee in target_employees:
            emp_id = employee.get("employee_id", "")
            if emp_id in submitted_author_ids:
                continue
            sent_count = sent_counts.get(emp_id, 0)
            if not self.can_send(sent_count=sent_count, max_reminders=max_reminders):
                continue
            recipients.append(
                {
                    "employee_id": emp_id,
                    "employee_name": employee.get("employee_name", ""),
                    "sent_count": sent_count,
                    "next_attempt": sent_count + 1,
                }
            )
        return recipients

    def can_send(self, *, sent_count: int, max_reminders: int) -> bool:
        """BR-WRP-012: 중복 발송 방지 — sent_count < max_reminders 이면 발송 가능."""
        return sent_count < max_reminders

    # ------------------------------------------------------------------
    # 트리거 시점 평가
    # ------------------------------------------------------------------

    def should_trigger(
        self,
        *,
        policy: ReminderPolicy,
        now_time: time,
    ) -> bool:
        """현재 시각이 리마인더 트리거 시점 이상인지 확인한다."""
        trigger_point = self._compute_trigger_time(policy)
        return now_time >= trigger_point

    def _compute_trigger_time(self, policy: ReminderPolicy) -> time:
        """정책에 따른 트리거 시각을 계산한다."""
        if policy.trigger_type == ReminderTrigger.FIXED_TIME:
            if policy.trigger_time is None:
                msg = "FIXED_TIME 트리거에는 trigger_time이 필요합니다"
                raise ValueError(msg)
            return policy.trigger_time

        # BEFORE/AFTER: deadline_time 을 기준으로 오프셋 계산
        base = self._time_to_minutes(policy.deadline_time)
        offset_minutes = policy.trigger_offset_hours * 60
        if policy.trigger_type == ReminderTrigger.BEFORE_DEADLINE:
            target = base - offset_minutes
        else:  # AFTER_DEADLINE
            target = base + offset_minutes
        # 같은 날 00:00~23:59 범위로 정규화
        target = max(0, min(target, 23 * 60 + 59))
        return self._minutes_to_time(target)

    @staticmethod
    def _time_to_minutes(t: time) -> int:
        return t.hour * 60 + t.minute

    @staticmethod
    def _minutes_to_time(total: int) -> time:
        return time(hour=total // 60, minute=total % 60)

    # ------------------------------------------------------------------
    # 통합 평가
    # ------------------------------------------------------------------

    def evaluate(
        self,
        *,
        policy: ReminderPolicy,
        now_time: time,
        target_date: date,
        target_employees: list[dict[str, Any]],
        submitted_author_ids: set[str],
        sent_counts: dict[str, int],
    ) -> dict[str, Any]:
        """정책+대상자+제출 현황을 종합하여 발송 대상을 결정한다."""
        triggered = self.should_trigger(policy=policy, now_time=now_time)
        if not triggered:
            return {
                "triggered": False,
                "target_date": target_date.isoformat(),
                "recipients": [],
            }

        recipients = self.identify_missing_submissions(
            target_employees=target_employees,
            submitted_author_ids=submitted_author_ids,
            sent_counts=sent_counts,
            max_reminders=policy.max_reminders,
        )
        logger.info(
            "리마인더 평가: 대상 %d명, 발송 대상 %d명, 기준일=%s",
            len(target_employees),
            len(recipients),
            target_date,
        )
        return {
            "triggered": True,
            "target_date": target_date.isoformat(),
            "deadline_time": policy.deadline_time.isoformat(timespec="minutes"),
            "recipients": recipients,
            "window_close": self._minutes_to_time(
                min(
                    23 * 60 + 59,
                    self._time_to_minutes(policy.deadline_time)
                    + int(timedelta(hours=6).total_seconds() // 60),
                )
            ).isoformat(timespec="minutes"),
        }
