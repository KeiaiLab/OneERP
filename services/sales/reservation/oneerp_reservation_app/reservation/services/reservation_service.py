"""예약 서비스 — 자원 예약 핵심 비즈니스 로직.

시간 충돌 검증, 반복 예약 생성, 체크인/체크아웃,
자동 해제 등 모든 BR-RSV-* 규칙을 구현한다.

비즈니스 규칙:
- BR-RSV-003: 동일 자원의 예약 시간 중복 불가
- BR-RSV-004: 과거 시간 예약 생성 불가
- BR-RSV-005: 예약은 시작 시간 이전에만 취소 가능
- BR-RSV-006: 반복 예약 시 각 인스턴스별 충돌 검증
- BR-RSV-007: 자원 이용 가능 시간 범위 내 예약
- BR-RSV-008: 정책 최대 예약 시간 초과 불가
- BR-RSV-009: 사전 예약 가능 일수 제한
- BR-RSV-010: 취소 마감 시간 이후 취소 불가

에러 코드:
- ERR-RSV-001: 시간 충돌
- ERR-RSV-002: 과거 시간 예약 시도
- ERR-RSV-003: 자원 비활성 상태
- ERR-RSV-004: 취소 불가 (이미 시작됨)
- ERR-RSV-005: 자원 미존재
- ERR-RSV-006: 이용 가능 시간 범위 벗어남
- ERR-RSV-007: 최대 예약 시간 초과
- ERR-RSV-008: 사전 예약 가능 일수 초과
- ERR-RSV-009: 동시 예약 수 초과
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_reservation_app.reservation.models.reservation import (
    RecurrenceType,
    Reservation,
    ReservationCreate,
    ReservationStatus,
)

logger = logging.getLogger(__name__)

# 기본 정책 값 (정책 문서가 없을 때 사용)
_DEFAULT_MAX_DURATION_MINUTES = 480
_DEFAULT_MAX_ADVANCE_DAYS = 90
_DEFAULT_CANCELLATION_DEADLINE_MINUTES = 30
_DEFAULT_MAX_CONCURRENT = 5
_DEFAULT_AUTO_RELEASE_MINUTES = 15


class ReservationService:
    """자원 예약 비즈니스 로직.

    예약 생성, 충돌 검증, 반복 예약, 체크인/아웃,
    자동 해제 등을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._reservation_repo = Repository("reservations", tenant_id=tenant_id)
        self._resource_repo = Repository("resources", tenant_id=tenant_id)
        self._policy_repo = Repository("reservation_policies", tenant_id=tenant_id)

    def _get_resource(self, resource_id: str) -> dict[str, Any]:
        """자원을 조회하고 존재하지 않으면 ERR-RSV-005 발생.

        BR-RSV-001 관련: 자원 존재 여부 검증.
        """
        resource = self._resource_repo.find_by_id(resource_id)
        if not resource:
            raise OneERPError(
                status_code=404,
                error="ERR-RSV-005",
                detail=f"자원 '{resource_id}'을(를) 찾을 수 없습니다",
            )
        return resource

    def _get_policy_for_resource(self, resource: dict[str, Any]) -> dict[str, Any]:
        """자원 유형에 해당하는 정책을 조회한다.

        정책이 없으면 기본값을 반환한다.
        """
        resource_type = resource.get("resource_type", "meeting_room")
        policies = self._policy_repo.find_many({"resource_type": resource_type}, limit=1)
        if policies:
            return policies[0]
        return {
            "max_duration_minutes": _DEFAULT_MAX_DURATION_MINUTES,
            "max_advance_days": _DEFAULT_MAX_ADVANCE_DAYS,
            "cancellation_deadline_minutes": _DEFAULT_CANCELLATION_DEADLINE_MINUTES,
            "max_concurrent_reservations": _DEFAULT_MAX_CONCURRENT,
            "auto_release_minutes": _DEFAULT_AUTO_RELEASE_MINUTES,
            "requires_approval": False,
        }

    def check_time_conflict(
        self,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
        *,
        exclude_reservation_id: str = "",
    ) -> bool:
        """동일 자원에 시간 충돌이 있는지 확인한다.

        BR-RSV-003: 동일 자원의 예약 시간 중복 불가.

        Returns:
            충돌이 있으면 True, 없으면 False
        """
        # 활성 상태의 예약만 확인 (취소/완료 제외)
        active_statuses = [
            ReservationStatus.DRAFT.value,
            ReservationStatus.CONFIRMED.value,
            ReservationStatus.IN_PROGRESS.value,
        ]
        existing = self._reservation_repo.find_many(
            {"resource_id": resource_id, "status": {"$in": active_statuses}},
            limit=10000,
        )

        for rsv in existing:
            rsv_id = rsv.get("_id", "")
            if exclude_reservation_id and rsv_id == exclude_reservation_id:
                continue

            rsv_start = rsv.get("start_time")
            rsv_end = rsv.get("end_time")
            if rsv_start is None or rsv_end is None:
                continue

            # datetime 문자열 → datetime 변환
            if isinstance(rsv_start, str):
                rsv_start = datetime.fromisoformat(rsv_start)
            if isinstance(rsv_end, str):
                rsv_end = datetime.fromisoformat(rsv_end)

            # 시간 겹침 조건: start1 < end2 AND start2 < end1
            if start_time < rsv_end and rsv_start < end_time:
                return True

        return False

    def validate_reservation(
        self,
        body: ReservationCreate,
        resource: dict[str, Any],
        policy: dict[str, Any],
        *,
        now: datetime | None = None,
    ) -> None:
        """예약 생성 전 모든 비즈니스 규칙을 검증한다.

        BR-RSV-003 ~ BR-RSV-009 를 검증한다.

        Raises:
            OneERPError: 규칙 위반 시
        """
        now = now or datetime.now(tz=UTC)

        # BR-RSV-004: 과거 시간 예약 불가
        if body.start_time <= now:
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-002",
                detail="과거 시간에는 예약을 생성할 수 없습니다",
            )

        # 시작 시간 < 종료 시간 검증
        if body.start_time >= body.end_time:
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-002",
                detail="종료 시간은 시작 시간보다 이후여야 합니다",
            )

        # BR-RSV-003: 자원 활성 상태 확인
        resource_status = resource.get("status", "active")
        if resource_status != "active":
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-003",
                detail=f"자원이 '{resource_status}' 상태이므로 예약할 수 없습니다",
            )

        # BR-RSV-008: 최대 예약 시간 초과 검증
        duration_minutes = (body.end_time - body.start_time).total_seconds() / 60
        max_duration = policy.get("max_duration_minutes", _DEFAULT_MAX_DURATION_MINUTES)
        if duration_minutes > max_duration:
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-007",
                detail=f"최대 예약 시간({max_duration}분)을 초과했습니다",
            )

        # BR-RSV-009: 사전 예약 가능 일수 제한
        max_advance_days = policy.get("max_advance_days", _DEFAULT_MAX_ADVANCE_DAYS)
        advance_days = (body.start_time - now).days
        if advance_days > max_advance_days:
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-008",
                detail=f"사전 예약 가능 일수({max_advance_days}일)를 초과했습니다",
            )

        # BR-RSV-007: 이용 가능 시간 범위 검증
        avail_start_str = resource.get("available_hours_start", "09:00")
        avail_end_str = resource.get("available_hours_end", "18:00")
        rsv_start_time = body.start_time.strftime("%H:%M")
        rsv_end_time = body.end_time.strftime("%H:%M")

        if rsv_start_time < avail_start_str or rsv_end_time > avail_end_str:
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-006",
                detail=(
                    f"자원 이용 가능 시간({avail_start_str}~{avail_end_str}) 범위를 벗어났습니다"
                ),
            )

        # BR-RSV-003: 시간 충돌 검증
        if self.check_time_conflict(body.resource_id, body.start_time, body.end_time):
            raise OneERPError(
                status_code=409,
                error="ERR-RSV-001",
                detail="해당 시간에 이미 예약이 존재합니다",
            )

        # 동시 예약 수 제한 확인
        if body.requester_id:
            max_concurrent = policy.get("max_concurrent_reservations", _DEFAULT_MAX_CONCURRENT)
            active_count = len(
                self._reservation_repo.find_many(
                    {
                        "requester_id": body.requester_id,
                        "status": {
                            "$in": [
                                ReservationStatus.DRAFT.value,
                                ReservationStatus.CONFIRMED.value,
                            ]
                        },
                    },
                    limit=max_concurrent + 1,
                )
            )
            if active_count >= max_concurrent:
                raise OneERPError(
                    status_code=400,
                    error="ERR-RSV-009",
                    detail=f"사용자당 최대 동시 예약 수({max_concurrent})를 초과했습니다",
                )

    def create_reservation(
        self,
        body: ReservationCreate,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """예약을 생성한다.

        BR-RSV-003 ~ BR-RSV-009 규칙을 검증 후 예약을 생성한다.
        반복 예약인 경우 여러 인스턴스를 생성한다.

        Returns:
            생성된 예약 정보 (reservation_ids, count)
        """
        resource = self._get_resource(body.resource_id)
        policy = self._get_policy_for_resource(resource)

        self.validate_reservation(body, resource, policy, now=now)

        created_ids: list[str] = []

        # BR-RSV-006: 반복 예약 처리
        if body.recurrence_type != RecurrenceType.NONE and body.recurrence_count > 1:
            parent_id = generate_name("RSV", tenant_id=self._tenant_id)
            for i in range(body.recurrence_count):
                offset = self._calculate_recurrence_offset(body.recurrence_type, i)
                instance_start = body.start_time + offset
                instance_end = body.end_time + offset

                # 각 인스턴스별 충돌 검증
                if self.check_time_conflict(body.resource_id, instance_start, instance_end):
                    logger.warning(
                        "반복 예약 충돌: resource=%s, 회차=%d",
                        body.resource_id,
                        i + 1,
                    )
                    continue

                rsv_id = parent_id if i == 0 else generate_name("RSV", tenant_id=self._tenant_id)
                doc = Reservation(
                    _id=rsv_id,
                    resource_id=body.resource_id,
                    title=body.title,
                    description=body.description,
                    requester_id=body.requester_id,
                    requester_name=body.requester_name,
                    start_time=instance_start,
                    end_time=instance_end,
                    status=ReservationStatus.CONFIRMED,
                    attendees=body.attendees,
                    recurrence_type=body.recurrence_type,
                    recurrence_count=body.recurrence_count,
                    parent_reservation_id=parent_id if i > 0 else "",
                    notes=body.notes,
                    tenant_id=self._tenant_id,
                )
                self._reservation_repo.insert(doc)
                created_ids.append(rsv_id)
        else:
            # 단일 예약
            rsv_id = generate_name("RSV", tenant_id=self._tenant_id)
            requires_approval = policy.get("requires_approval", False)
            initial_status = (
                ReservationStatus.DRAFT if requires_approval else ReservationStatus.CONFIRMED
            )

            doc = Reservation(
                _id=rsv_id,
                resource_id=body.resource_id,
                title=body.title,
                description=body.description,
                requester_id=body.requester_id,
                requester_name=body.requester_name,
                start_time=body.start_time,
                end_time=body.end_time,
                status=initial_status,
                attendees=body.attendees,
                recurrence_type=RecurrenceType.NONE,
                recurrence_count=1,
                notes=body.notes,
                tenant_id=self._tenant_id,
            )
            self._reservation_repo.insert(doc)
            created_ids.append(rsv_id)

        logger.info(
            "예약 생성 완료: resource=%s, 건수=%d",
            body.resource_id,
            len(created_ids),
        )

        return {
            "reservation_ids": created_ids,
            "count": len(created_ids),
            "resource_id": body.resource_id,
        }

    def cancel_reservation(
        self,
        reservation_id: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """예약을 취소한다.

        BR-RSV-005: 시작 시간 이전에만 취소 가능.
        BR-RSV-010: 취소 마감 시간 이후에는 취소 불가.

        Returns:
            취소 결과 정보
        """
        now = now or datetime.now(tz=UTC)
        rsv = self._reservation_repo.find_by_id(reservation_id)
        if not rsv:
            raise OneERPError(
                status_code=404,
                error="ERR-RSV-005",
                detail=f"예약 '{reservation_id}'을(를) 찾을 수 없습니다",
            )

        status = rsv.get("status", "")
        if status in (
            ReservationStatus.COMPLETED.value,
            ReservationStatus.CANCELLED.value,
        ):
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-004",
                detail="이미 완료되었거나 취소된 예약입니다",
            )

        start_time = rsv.get("start_time")
        if start_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if start_time <= now:
                raise OneERPError(
                    status_code=400,
                    error="ERR-RSV-004",
                    detail="이미 시작된 예약은 취소할 수 없습니다",
                )

            # 취소 마감 시간 검증
            resource_id = rsv.get("resource_id", "")
            if resource_id:
                resource = self._resource_repo.find_by_id(resource_id)
                if resource:
                    policy = self._get_policy_for_resource(resource)
                    deadline_minutes = policy.get(
                        "cancellation_deadline_minutes",
                        _DEFAULT_CANCELLATION_DEADLINE_MINUTES,
                    )
                    deadline = start_time - timedelta(minutes=deadline_minutes)
                    if now > deadline:
                        raise OneERPError(
                            status_code=400,
                            error="ERR-RSV-004",
                            detail=(f"취소 마감 시간(시작 {deadline_minutes}분 전)이 지났습니다"),
                        )

        self._reservation_repo.update_by_id(
            reservation_id, {"status": ReservationStatus.CANCELLED.value}
        )

        logger.info("예약 취소: %s", reservation_id)
        return {"reservation_id": reservation_id, "status": "cancelled"}

    def check_in(
        self,
        reservation_id: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """예약 체크인을 처리한다.

        확인된(confirmed) 예약만 체크인 가능.

        Returns:
            체크인 결과 정보
        """
        now = now or datetime.now(tz=UTC)
        rsv = self._reservation_repo.find_by_id(reservation_id)
        if not rsv:
            raise OneERPError(
                status_code=404,
                error="ERR-RSV-005",
                detail=f"예약 '{reservation_id}'을(를) 찾을 수 없습니다",
            )

        status = rsv.get("status", "")
        if status != ReservationStatus.CONFIRMED.value:
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-004",
                detail=f"'{status}' 상태에서는 체크인할 수 없습니다",
            )

        self._reservation_repo.update_by_id(
            reservation_id,
            {
                "status": ReservationStatus.IN_PROGRESS.value,
                "checked_in": True,
                "checked_in_at": now,
            },
        )

        logger.info("예약 체크인: %s", reservation_id)
        return {
            "reservation_id": reservation_id,
            "status": "in_progress",
            "checked_in_at": now.isoformat(),
        }

    def check_out(
        self,
        reservation_id: str,
    ) -> dict[str, Any]:
        """예약 체크아웃(완료)을 처리한다.

        진행 중(in_progress) 예약만 체크아웃 가능.

        Returns:
            체크아웃 결과 정보
        """
        rsv = self._reservation_repo.find_by_id(reservation_id)
        if not rsv:
            raise OneERPError(
                status_code=404,
                error="ERR-RSV-005",
                detail=f"예약 '{reservation_id}'을(를) 찾을 수 없습니다",
            )

        status = rsv.get("status", "")
        if status != ReservationStatus.IN_PROGRESS.value:
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-004",
                detail=f"'{status}' 상태에서는 체크아웃할 수 없습니다",
            )

        self._reservation_repo.update_by_id(
            reservation_id,
            {"status": ReservationStatus.COMPLETED.value},
        )

        logger.info("예약 체크아웃: %s", reservation_id)
        return {"reservation_id": reservation_id, "status": "completed"}

    def release_no_shows(
        self,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """미체크인 예약을 자동 해제한다.

        시작 시간 이후 auto_release_minutes가 경과한
        confirmed 상태의 예약을 no_show로 변경한다.

        Returns:
            해제된 예약 수
        """
        now = now or datetime.now(tz=UTC)
        confirmed = self._reservation_repo.find_many(
            {"status": ReservationStatus.CONFIRMED.value},
            limit=10000,
        )

        released_count = 0
        for rsv in confirmed:
            start_time = rsv.get("start_time")
            if not start_time:
                continue
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)

            resource_id = rsv.get("resource_id", "")
            auto_release = _DEFAULT_AUTO_RELEASE_MINUTES
            if resource_id:
                resource = self._resource_repo.find_by_id(resource_id)
                if resource:
                    policy = self._get_policy_for_resource(resource)
                    auto_release = policy.get("auto_release_minutes", _DEFAULT_AUTO_RELEASE_MINUTES)

            deadline = start_time + timedelta(minutes=auto_release)
            if now >= deadline:
                rsv_id = rsv.get("_id", "")
                self._reservation_repo.update_by_id(
                    rsv_id, {"status": ReservationStatus.NO_SHOW.value}
                )
                released_count += 1
                logger.info("미체크인 자동 해제: %s", rsv_id)

        return {"released_count": released_count}

    def get_resource_availability(
        self,
        resource_id: str,
        date_str: str,
    ) -> dict[str, Any]:
        """특정 자원의 특정 날짜 가용성을 조회한다.

        Returns:
            예약 목록과 빈 시간대 정보
        """
        resource = self._get_resource(resource_id)
        avail_start = resource.get("available_hours_start", "09:00")
        avail_end = resource.get("available_hours_end", "18:00")

        # 해당 날짜의 활성 예약 목록 조회
        active_statuses = [
            ReservationStatus.CONFIRMED.value,
            ReservationStatus.IN_PROGRESS.value,
        ]
        reservations = self._reservation_repo.find_many(
            {"resource_id": resource_id, "status": {"$in": active_statuses}},
            limit=100,
        )

        # 해당 날짜 필터링
        day_reservations = []
        for rsv in reservations:
            start = rsv.get("start_time")
            if start:
                if isinstance(start, str):
                    start = datetime.fromisoformat(start)
                if start.strftime("%Y-%m-%d") == date_str:
                    day_reservations.append(rsv)

        return {
            "resource_id": resource_id,
            "date": date_str,
            "available_hours": f"{avail_start}~{avail_end}",
            "reservation_count": len(day_reservations),
            "reservations": day_reservations,
        }

    @staticmethod
    def _calculate_recurrence_offset(
        recurrence_type: RecurrenceType,
        index: int,
    ) -> timedelta:
        """반복 유형에 따른 시간 오프셋을 계산한다."""
        if recurrence_type == RecurrenceType.DAILY:
            return timedelta(days=index)
        if recurrence_type == RecurrenceType.WEEKLY:
            return timedelta(weeks=index)
        if recurrence_type == RecurrenceType.MONTHLY:
            return timedelta(days=30 * index)
        return timedelta()
