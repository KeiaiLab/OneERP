"""캘린더 이벤트 서비스 — 이벤트 CRUD, 초대, 충돌 검사, 반복 생성 비즈니스 로직.

BR-CAL-010: 이벤트는 반드시 캘린더에 속해야 한다.
BR-CAL-011: 종료 시각은 시작 시각 이후여야 한다.
BR-CAL-014: 이벤트 상태 전이: draft → confirmed → cancelled.
BR-CAL-021: 동일 이벤트에 동일 사용자 중복 초대 불가.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 이벤트 상태 전환 규칙 (BR-CAL-014)
_VALID_EVENT_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"confirmed", "cancelled"},
    "confirmed": {"cancelled"},
}


class EventService:
    """캘린더 이벤트 비즈니스 로직.

    이벤트 생성, 상태 전환, 충돌 검사, 초대자 관리, 반복 생성을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._event_repo = Repository("calendar_events", tenant_id=tenant_id)
        self._calendar_repo = Repository("calendars", tenant_id=tenant_id)
        self._invitee_repo = Repository("invitees", tenant_id=tenant_id)

    def check_calendar_exists(self, calendar_id: str) -> dict[str, Any]:
        """BR-CAL-010: 캘린더 존재 확인.

        Returns:
            캘린더 문서

        Raises:
            ValueError: ERR-CAL-010 — 캘린더를 찾을 수 없는 경우
        """
        cal = self._calendar_repo.find_by_id(calendar_id)
        if not cal:
            msg = f"캘린더 '{calendar_id}'를 찾을 수 없습니다 (ERR-CAL-010)"
            raise ValueError(msg)
        return cal

    def change_event_status(
        self,
        event_id: str,
        new_status: str,
    ) -> dict[str, Any]:
        """BR-CAL-014: 이벤트 상태를 전환한다.

        허용 전환: draft → confirmed/cancelled, confirmed → cancelled.

        Args:
            event_id: 이벤트 ID
            new_status: 새 상태

        Returns:
            전환 결과

        Raises:
            ValueError: ERR-CAL-014 — 유효하지 않은 상태 전환
        """
        event = self._event_repo.find_by_id(event_id)
        if not event:
            msg = f"이벤트 '{event_id}'를 찾을 수 없습니다 (ERR-CAL-011)"
            raise ValueError(msg)

        current = event.get("status", "draft")
        allowed = _VALID_EVENT_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            msg = f"'{current}'에서 '{new_status}'(으)로 전환할 수 없습니다 (ERR-CAL-014)"
            raise ValueError(msg)

        self._event_repo.update_by_id(event_id, {"status": new_status})
        logger.info("이벤트 상태 변경: %s %s → %s", event_id, current, new_status)
        return {
            "event_id": event_id,
            "previous_status": current,
            "new_status": new_status,
        }

    def detect_conflicts(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
        *,
        exclude_event_id: str = "",
    ) -> list[dict[str, Any]]:
        """시간 충돌 검사 — 사용자의 기존 이벤트와 겹치는 일정을 반환한다.

        BR-CAL-015: 충돌 이벤트는 경고 수준으로 반환 (차단하지 않음).

        Args:
            user_id: 사용자 ID
            start_dt: 검사 시작 일시
            end_dt: 검사 종료 일시
            exclude_event_id: 제외할 이벤트 ID (수정 시)

        Returns:
            충돌하는 이벤트 목록
        """
        # 사용자가 주최자이거나 초대받은 이벤트 조회
        user_events = self._event_repo.find_many(
            {
                "organizer_id": user_id,
                "status": {"$ne": "cancelled"},
            },
            limit=1000,
        )

        conflicts: list[dict[str, Any]] = []
        for evt in user_events:
            if exclude_event_id and evt.get("_id") == exclude_event_id:
                continue

            evt_start = evt.get("start_dt")
            evt_end = evt.get("end_dt")
            if not evt_start or not evt_end:
                continue

            # datetime 문자열 → datetime 변환
            if isinstance(evt_start, str):
                evt_start = datetime.fromisoformat(evt_start)
            if isinstance(evt_end, str):
                evt_end = datetime.fromisoformat(evt_end)

            # 시간 범위 겹침 확인
            if evt_start < end_dt and evt_end > start_dt:
                conflicts.append(
                    {
                        "event_id": evt.get("_id", ""),
                        "title": evt.get("title", ""),
                        "start_dt": str(evt_start),
                        "end_dt": str(evt_end),
                    }
                )

        return conflicts

    def add_invitee(
        self,
        event_id: str,
        user_id: str,
        user_name: str = "",
        email: str = "",
        *,
        is_required: bool = True,
    ) -> dict[str, Any]:
        """BR-CAL-021: 이벤트에 초대자를 추가한다.

        동일 사용자 중복 초대를 방지한다.

        Args:
            event_id: 이벤트 ID
            user_id: 초대할 사용자 ID
            user_name: 사용자 이름
            email: 이메일
            is_required: 필수 참석 여부

        Returns:
            초대 결과

        Raises:
            ValueError: ERR-CAL-021 — 이미 초대된 사용자
        """
        event = self._event_repo.find_by_id(event_id)
        if not event:
            msg = f"이벤트 '{event_id}'를 찾을 수 없습니다 (ERR-CAL-011)"
            raise ValueError(msg)

        # 중복 체크
        existing = self._invitee_repo.find_many(
            {"event_id": event_id, "user_id": user_id},
            limit=1,
        )
        if existing:
            msg = f"사용자 '{user_id}'는 이미 초대되었습니다 (ERR-CAL-021)"
            raise ValueError(msg)

        invitee_data = {
            "event_id": event_id,
            "user_id": user_id,
            "user_name": user_name,
            "email": email,
            "is_required": is_required,
            "response_status": "pending",
            "tenant_id": self._tenant_id,
        }
        self._invitee_repo.insert(invitee_data)
        logger.info("초대자 추가: 이벤트=%s, 사용자=%s", event_id, user_id)
        return {"event_id": event_id, "user_id": user_id, "status": "pending"}

    def respond_to_invite(
        self,
        event_id: str,
        user_id: str,
        response_status: str,
        response_comment: str = "",
    ) -> dict[str, Any]:
        """BR-CAL-022: 초대 응답을 처리한다.

        Args:
            event_id: 이벤트 ID
            user_id: 응답하는 사용자 ID
            response_status: accepted/declined/tentative
            response_comment: 응답 코멘트

        Returns:
            응답 결과

        Raises:
            ValueError: 초대 정보가 없는 경우
        """
        invitees = self._invitee_repo.find_many(
            {"event_id": event_id, "user_id": user_id},
            limit=1,
        )
        if not invitees:
            msg = f"사용자 '{user_id}'의 초대 정보를 찾을 수 없습니다 (ERR-CAL-022)"
            raise ValueError(msg)

        invitee = invitees[0]
        valid_responses = {"accepted", "declined", "tentative"}
        if response_status not in valid_responses:
            msg = f"유효하지 않은 응답 상태입니다: {response_status} (ERR-CAL-022)"
            raise ValueError(msg)

        self._invitee_repo.update_by_id(
            invitee["_id"],
            {
                "response_status": response_status,
                "response_comment": response_comment,
            },
        )
        logger.info(
            "초대 응답: 이벤트=%s, 사용자=%s, 응답=%s",
            event_id,
            user_id,
            response_status,
        )
        return {
            "event_id": event_id,
            "user_id": user_id,
            "response_status": response_status,
        }

    def generate_recurring_events(
        self,
        event_id: str,
    ) -> list[dict[str, Any]]:
        """BR-CAL-013: 반복 이벤트 인스턴스를 생성한다.

        반복 규칙에 따라 최대 count 또는 end_date까지 이벤트를 생성한다.

        Args:
            event_id: 원본 반복 이벤트 ID

        Returns:
            생성된 이벤트 목록

        Raises:
            ValueError: 반복 규칙이 없는 경우
        """
        event = self._event_repo.find_by_id(event_id)
        if not event:
            msg = f"이벤트 '{event_id}'를 찾을 수 없습니다 (ERR-CAL-011)"
            raise ValueError(msg)

        frequency = event.get("recurrence_frequency")
        if not frequency:
            msg = f"이벤트 '{event_id}'에 반복 규칙이 없습니다 (ERR-CAL-013)"
            raise ValueError(msg)

        interval = event.get("recurrence_interval", 1)
        count = event.get("recurrence_count") or 10  # 기본 최대 10회
        end_date_raw = event.get("recurrence_end_date")
        start_dt_raw = event.get("start_dt")
        end_dt_raw = event.get("end_dt")

        if not start_dt_raw or not end_dt_raw:
            msg = "시작/종료 일시가 필요합니다 (ERR-CAL-010)"
            raise ValueError(msg)

        if isinstance(start_dt_raw, str):
            start_dt_raw = datetime.fromisoformat(start_dt_raw)
        if isinstance(end_dt_raw, str):
            end_dt_raw = datetime.fromisoformat(end_dt_raw)

        duration = end_dt_raw - start_dt_raw
        end_date = None
        if end_date_raw:
            end_date = (
                datetime.fromisoformat(end_date_raw)
                if isinstance(end_date_raw, str)
                else end_date_raw
            )

        # 주기별 timedelta 계산
        delta_map = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),  # 근사값
            "yearly": timedelta(days=365),
        }
        base_delta = delta_map.get(frequency, timedelta(days=1))

        generated: list[dict[str, Any]] = []
        current_start = start_dt_raw

        for i in range(1, count + 1):
            current_start = current_start + base_delta * interval
            if end_date and current_start > end_date:
                break

            new_event = {
                "calendar_id": event.get("calendar_id", ""),
                "title": event.get("title", ""),
                "description": event.get("description", ""),
                "event_type": event.get("event_type", "meeting"),
                "start_dt": current_start.isoformat(),
                "end_dt": (current_start + duration).isoformat(),
                "all_day": event.get("all_day", False),
                "location": event.get("location", ""),
                "organizer_id": event.get("organizer_id", ""),
                "status": "draft",
                "ref_doctype": "calendar_event",
                "ref_docname": event_id,
                "tenant_id": self._tenant_id,
            }
            self._event_repo.insert(new_event)
            generated.append(
                {
                    "index": i,
                    "start_dt": current_start.isoformat(),
                    "end_dt": (current_start + duration).isoformat(),
                }
            )

        logger.info(
            "반복 이벤트 생성: 원본=%s, 생성=%d건",
            event_id,
            len(generated),
        )
        return generated

    def get_events_in_range(
        self,
        calendar_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict[str, Any]]:
        """기간 내 이벤트를 조회한다.

        Args:
            calendar_id: 캘린더 ID
            start_dt: 조회 시작 일시
            end_dt: 조회 종료 일시

        Returns:
            기간 내 이벤트 목록
        """
        events = self._event_repo.find_many(
            {
                "calendar_id": calendar_id,
                "status": {"$ne": "cancelled"},
            },
            limit=10000,
        )

        result: list[dict[str, Any]] = []
        for evt in events:
            evt_start = evt.get("start_dt")
            evt_end = evt.get("end_dt")
            if not evt_start or not evt_end:
                continue

            if isinstance(evt_start, str):
                evt_start = datetime.fromisoformat(evt_start)
            if isinstance(evt_end, str):
                evt_end = datetime.fromisoformat(evt_end)

            if evt_start < end_dt and evt_end > start_dt:
                result.append(evt)

        return result
