"""업무보고 리마인더(미제출자 식별) 서비스 단위 테스트.

대상 비즈니스 룰:
- BR-WRP-012: 리마인더 최대 알림 횟수 제한 (max_reminders)
- 계산 로직 4.5: 미제출자 식별
"""

from __future__ import annotations

from datetime import date, time

import pytest
from oneerp_learning_app.workreport.services.reminder_identification_service import (
    ReminderIdentificationService,
    ReminderPolicy,
    ReminderTrigger,
)


class Test미제출자_식별:
    """계산 로직 4.5."""

    def test_대상자중_미제출_식별(self) -> None:
        service = ReminderIdentificationService()
        result = service.identify_missing_submissions(
            target_employees=[
                {"employee_id": "EMP-001", "employee_name": "홍길동"},
                {"employee_id": "EMP-002", "employee_name": "김영희"},
                {"employee_id": "EMP-003", "employee_name": "박철수"},
            ],
            submitted_author_ids={"EMP-002"},
            sent_counts={},
            max_reminders=2,
        )
        emps = [r["employee_id"] for r in result]
        assert "EMP-001" in emps
        assert "EMP-003" in emps
        assert "EMP-002" not in emps

    def test_최대_알림_횟수_초과자_제외(self) -> None:
        """BR-WRP-012: sent_count >= max_reminders 직원은 제외."""
        service = ReminderIdentificationService()
        result = service.identify_missing_submissions(
            target_employees=[
                {"employee_id": "EMP-001", "employee_name": "홍길동"},
                {"employee_id": "EMP-002", "employee_name": "김영희"},
            ],
            submitted_author_ids=set(),
            sent_counts={"EMP-001": 2, "EMP-002": 0},
            max_reminders=2,
        )
        emps = [r["employee_id"] for r in result]
        assert "EMP-002" in emps
        assert "EMP-001" not in emps

    def test_전원_제출시_빈_결과(self) -> None:
        service = ReminderIdentificationService()
        result = service.identify_missing_submissions(
            target_employees=[
                {"employee_id": "EMP-001", "employee_name": "홍길동"},
            ],
            submitted_author_ids={"EMP-001"},
            sent_counts={},
            max_reminders=2,
        )
        assert result == []

    def test_sent_count_누적_반환(self) -> None:
        service = ReminderIdentificationService()
        result = service.identify_missing_submissions(
            target_employees=[
                {"employee_id": "EMP-001", "employee_name": "홍길동"},
            ],
            submitted_author_ids=set(),
            sent_counts={"EMP-001": 1},
            max_reminders=3,
        )
        assert len(result) == 1
        assert result[0]["sent_count"] == 1


class Test리마인더_정책_트리거:
    """ReportReminder 정책 평가."""

    def test_기한전_트리거_시간_도달(self) -> None:
        """trigger_type=before_deadline, 기한 2시간 전."""
        policy = ReminderPolicy(
            trigger_type=ReminderTrigger.BEFORE_DEADLINE,
            trigger_offset_hours=2,
            deadline_time=time(18, 0),
            trigger_time=None,
            max_reminders=2,
        )
        service = ReminderIdentificationService()
        # 현재 시각이 16:00 — 정확히 기한 2시간 전
        assert (
            service.should_trigger(
                policy=policy,
                now_time=time(16, 0),
            )
            is True
        )
        # 15:00 — 아직 트리거 시점 이전
        assert (
            service.should_trigger(
                policy=policy,
                now_time=time(15, 0),
            )
            is False
        )
        # 16:30 — 트리거 이후
        assert (
            service.should_trigger(
                policy=policy,
                now_time=time(16, 30),
            )
            is True
        )

    def test_기한후_트리거(self) -> None:
        policy = ReminderPolicy(
            trigger_type=ReminderTrigger.AFTER_DEADLINE,
            trigger_offset_hours=1,
            deadline_time=time(18, 0),
            trigger_time=None,
            max_reminders=2,
        )
        service = ReminderIdentificationService()
        assert service.should_trigger(policy=policy, now_time=time(19, 0)) is True
        assert service.should_trigger(policy=policy, now_time=time(18, 30)) is False

    def test_고정시각_트리거(self) -> None:
        policy = ReminderPolicy(
            trigger_type=ReminderTrigger.FIXED_TIME,
            trigger_offset_hours=0,
            deadline_time=time(18, 0),
            trigger_time=time(17, 30),
            max_reminders=2,
        )
        service = ReminderIdentificationService()
        assert service.should_trigger(policy=policy, now_time=time(17, 30)) is True
        assert service.should_trigger(policy=policy, now_time=time(17, 0)) is False

    def test_잘못된_고정시각_설정(self) -> None:
        """FIXED_TIME 이면서 trigger_time 누락 시 ValueError."""
        policy = ReminderPolicy(
            trigger_type=ReminderTrigger.FIXED_TIME,
            trigger_offset_hours=0,
            deadline_time=time(18, 0),
            trigger_time=None,
            max_reminders=2,
        )
        service = ReminderIdentificationService()
        with pytest.raises(ValueError, match="trigger_time"):
            service.should_trigger(policy=policy, now_time=time(17, 0))


class Test중복발송_방지:
    """ReminderLog 기반 중복 발송 방지."""

    def test_아직_발송가능(self) -> None:
        service = ReminderIdentificationService()
        assert service.can_send(sent_count=0, max_reminders=2) is True
        assert service.can_send(sent_count=1, max_reminders=2) is True

    def test_최대치_도달(self) -> None:
        service = ReminderIdentificationService()
        assert service.can_send(sent_count=2, max_reminders=2) is False
        assert service.can_send(sent_count=5, max_reminders=2) is False


class Test통합_식별:
    """Policy + 대상자 + sent_counts 통합."""

    def test_트리거_미도달이면_대상자_0명(self) -> None:
        service = ReminderIdentificationService()
        policy = ReminderPolicy(
            trigger_type=ReminderTrigger.BEFORE_DEADLINE,
            trigger_offset_hours=2,
            deadline_time=time(18, 0),
            trigger_time=None,
            max_reminders=2,
        )
        result = service.evaluate(
            policy=policy,
            now_time=time(10, 0),  # 트리거는 16:00
            target_date=date(2026, 4, 10),
            target_employees=[
                {"employee_id": "EMP-001", "employee_name": "홍길동"},
            ],
            submitted_author_ids=set(),
            sent_counts={},
        )
        assert result["triggered"] is False
        assert result["recipients"] == []

    def test_트리거_도달시_미제출자_반환(self) -> None:
        service = ReminderIdentificationService()
        policy = ReminderPolicy(
            trigger_type=ReminderTrigger.BEFORE_DEADLINE,
            trigger_offset_hours=2,
            deadline_time=time(18, 0),
            trigger_time=None,
            max_reminders=2,
        )
        result = service.evaluate(
            policy=policy,
            now_time=time(16, 0),
            target_date=date(2026, 4, 10),
            target_employees=[
                {"employee_id": "EMP-001", "employee_name": "홍길동"},
                {"employee_id": "EMP-002", "employee_name": "김영희"},
            ],
            submitted_author_ids={"EMP-002"},
            sent_counts={"EMP-001": 0},
        )
        assert result["triggered"] is True
        assert len(result["recipients"]) == 1
        assert result["recipients"][0]["employee_id"] == "EMP-001"
