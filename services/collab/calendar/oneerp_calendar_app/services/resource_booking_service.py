"""자원 예약 서비스 — 회의실/장비 예약, 충돌 검사, 가용성 조회.

BR-CAL-050: 자원 예약은 이벤트 및 자원에 연결되어야 한다.
BR-CAL-051: 동일 자원의 시간 중복 예약 불가.
BR-CAL-052: 예약 종료 시각은 시작 시각 이후여야 한다.
BR-CAL-053: 유지보수/폐기 상태 자원은 예약 불가.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ResourceBookingService:
    """자원 예약 비즈니스 로직.

    자원 가용성 확인, 예약 충돌 검사, 예약 상태 관리를 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._resource_repo = Repository("resources", tenant_id=tenant_id)
        self._booking_repo = Repository("resource_bookings", tenant_id=tenant_id)

    def check_resource_available(self, resource_id: str) -> dict[str, Any]:
        """BR-CAL-053: 자원이 예약 가능 상태인지 확인한다.

        Returns:
            자원 문서

        Raises:
            ValueError: ERR-CAL-040 — 자원을 찾을 수 없음
            ValueError: ERR-CAL-053 — 예약 불가 상태
        """
        resource = self._resource_repo.find_by_id(resource_id)
        if not resource:
            msg = f"자원 '{resource_id}'를 찾을 수 없습니다 (ERR-CAL-040)"
            raise ValueError(msg)

        status = resource.get("status", "available")
        if status != "available":
            msg = f"자원 '{resource_id}'는 '{status}' 상태로 예약할 수 없습니다 (ERR-CAL-053)"
            raise ValueError(msg)

        return resource

    def check_booking_conflict(
        self,
        resource_id: str,
        start_dt: datetime,
        end_dt: datetime,
        *,
        exclude_booking_id: str = "",
    ) -> list[dict[str, Any]]:
        """BR-CAL-051: 자원의 시간 중복 예약을 검사한다.

        Args:
            resource_id: 자원 ID
            start_dt: 예약 시작 일시
            end_dt: 예약 종료 일시
            exclude_booking_id: 제외할 예약 ID (수정 시)

        Returns:
            충돌하는 예약 목록
        """
        bookings = self._booking_repo.find_many(
            {
                "resource_id": resource_id,
                "status": {"$ne": "cancelled"},
            },
            limit=1000,
        )

        conflicts: list[dict[str, Any]] = []
        for bk in bookings:
            if exclude_booking_id and bk.get("_id") == exclude_booking_id:
                continue

            bk_start = bk.get("start_dt")
            bk_end = bk.get("end_dt")
            if not bk_start or not bk_end:
                continue

            if isinstance(bk_start, str):
                bk_start = datetime.fromisoformat(bk_start)
            if isinstance(bk_end, str):
                bk_end = datetime.fromisoformat(bk_end)

            if bk_start < end_dt and bk_end > start_dt:
                conflicts.append(
                    {
                        "booking_id": bk.get("_id", ""),
                        "event_id": bk.get("event_id", ""),
                        "start_dt": str(bk_start),
                        "end_dt": str(bk_end),
                    }
                )

        return conflicts

    def book_resource(
        self,
        event_id: str,
        resource_id: str,
        start_dt: datetime,
        end_dt: datetime,
        booked_by: str = "",
    ) -> dict[str, Any]:
        """BR-CAL-050: 자원을 예약한다.

        자원 가용성 및 충돌 검사 후 예약을 생성한다.

        Args:
            event_id: 이벤트 ID
            resource_id: 자원 ID
            start_dt: 시작 일시
            end_dt: 종료 일시
            booked_by: 예약자 ID

        Returns:
            예약 결과

        Raises:
            ValueError: ERR-CAL-051 — 시간 충돌
        """
        # 자원 가용성 확인
        self.check_resource_available(resource_id)

        # 충돌 검사
        conflicts = self.check_booking_conflict(resource_id, start_dt, end_dt)
        if conflicts:
            msg = (
                f"자원 '{resource_id}'에 시간이 겹치는 예약이 있습니다 "
                f"({len(conflicts)}건) (ERR-CAL-051)"
            )
            raise ValueError(msg)

        booking_data = {
            "event_id": event_id,
            "resource_id": resource_id,
            "start_dt": start_dt.isoformat(),
            "end_dt": end_dt.isoformat(),
            "booked_by": booked_by,
            "status": "confirmed",
            "tenant_id": self._tenant_id,
        }
        booking_id = self._booking_repo.insert(booking_data)

        logger.info(
            "자원 예약 완료: 자원=%s, 이벤트=%s, %s~%s",
            resource_id,
            event_id,
            start_dt,
            end_dt,
        )
        return {
            "booking_id": booking_id,
            "resource_id": resource_id,
            "event_id": event_id,
            "status": "confirmed",
        }

    def list_bookings(
        self,
        *,
        resource_id: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """자원 예약 목록을 페이지네이션으로 조회한다."""
        query: dict[str, Any] = {}
        if resource_id:
            query["resource_id"] = resource_id
        skip = (page - 1) * page_size
        docs = self._booking_repo.find_many(
            query, skip=skip, limit=page_size, sort=[("start_dt", -1)]
        )
        total_count = self._booking_repo.count(query)
        return {"data": docs, "total": total_count, "page": page, "page_size": page_size}

    def cancel_booking(self, booking_id: str) -> dict[str, Any]:
        """예약을 취소한다.

        Args:
            booking_id: 예약 ID

        Returns:
            취소 결과

        Raises:
            ValueError: 예약을 찾을 수 없는 경우
        """
        booking = self._booking_repo.find_by_id(booking_id)
        if not booking:
            msg = f"예약 '{booking_id}'를 찾을 수 없습니다 (ERR-CAL-050)"
            raise ValueError(msg)

        if booking.get("status") == "cancelled":
            msg = f"예약 '{booking_id}'은 이미 취소되었습니다 (ERR-CAL-050)"
            raise ValueError(msg)

        self._booking_repo.update_by_id(booking_id, {"status": "cancelled"})
        logger.info("자원 예약 취소: %s", booking_id)
        return {"booking_id": booking_id, "status": "cancelled"}

    def get_resource_availability(
        self,
        resource_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict[str, Any]:
        """자원의 특정 기간 가용 시간대를 반환한다.

        Args:
            resource_id: 자원 ID
            start_dt: 조회 시작 일시
            end_dt: 조회 종료 일시

        Returns:
            가용 여부 및 예약된 시간대
        """
        self.check_resource_available(resource_id)

        bookings = self._booking_repo.find_many(
            {
                "resource_id": resource_id,
                "status": {"$ne": "cancelled"},
            },
            limit=1000,
        )

        booked_slots: list[dict[str, str]] = []
        for bk in bookings:
            bk_start = bk.get("start_dt")
            bk_end = bk.get("end_dt")
            if not bk_start or not bk_end:
                continue

            if isinstance(bk_start, str):
                bk_start = datetime.fromisoformat(bk_start)
            if isinstance(bk_end, str):
                bk_end = datetime.fromisoformat(bk_end)

            if bk_start < end_dt and bk_end > start_dt:
                booked_slots.append(
                    {
                        "start_dt": str(bk_start),
                        "end_dt": str(bk_end),
                    }
                )

        return {
            "resource_id": resource_id,
            "period_start": str(start_dt),
            "period_end": str(end_dt),
            "booked_slots": booked_slots,
            "total_bookings": len(booked_slots),
        }
