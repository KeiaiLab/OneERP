"""자원 관리 서비스 — 자원 생성/수정/비활성화 비즈니스 로직.

비즈니스 규칙:
- BR-RSV-001: 자원명은 테넌트 내에서 고유해야 한다
- BR-RSV-002: 자원은 활성 예약이 없을 때만 비활성화 가능
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.repository import Repository

from oneerp_reservation_app.reservation.models.reservation import ReservationStatus

logger = logging.getLogger(__name__)


class ResourceService:
    """자원 마스터 비즈니스 로직.

    자원 등록, 고유명 검증, 비활성화 규칙을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._resource_repo = Repository("resources", tenant_id=tenant_id)
        self._reservation_repo = Repository("reservations", tenant_id=tenant_id)

    def validate_unique_name(self, name: str, *, exclude_id: str = "") -> None:
        """자원명 고유성을 검증한다.

        BR-RSV-001: 자원명은 테넌트 내에서 고유해야 한다.

        Raises:
            OneERPError: 동일 이름의 자원이 이미 존재할 때
        """
        existing = self._resource_repo.find_many({"name": name}, limit=1)
        for doc in existing:
            if exclude_id and doc.get("_id") == exclude_id:
                continue
            raise OneERPError(
                status_code=409,
                error="ERR-RSV-001",
                detail=f"자원명 '{name}'이(가) 이미 존재합니다",
            )

    def can_deactivate(self, resource_id: str) -> bool:
        """자원을 비활성화할 수 있는지 확인한다.

        BR-RSV-002: 활성 예약이 있으면 비활성화 불가.

        Returns:
            비활성화 가능 여부
        """
        active_statuses = [
            ReservationStatus.CONFIRMED.value,
            ReservationStatus.IN_PROGRESS.value,
        ]
        active_reservations = self._reservation_repo.find_many(
            {"resource_id": resource_id, "status": {"$in": active_statuses}},
            limit=1,
        )
        return len(active_reservations) == 0

    def deactivate_resource(self, resource_id: str) -> dict[str, Any]:
        """자원을 비활성화한다.

        BR-RSV-002: 활성 예약이 없을 때만 비활성화 가능.

        Returns:
            비활성화 결과 정보

        Raises:
            OneERPError: 활성 예약이 있을 때
        """
        resource = self._resource_repo.find_by_id(resource_id)
        if not resource:
            raise OneERPError(
                status_code=404,
                error="ERR-RSV-005",
                detail=f"자원 '{resource_id}'을(를) 찾을 수 없습니다",
            )

        if not self.can_deactivate(resource_id):
            raise OneERPError(
                status_code=400,
                error="ERR-RSV-003",
                detail="활성 예약이 있어 비활성화할 수 없습니다",
            )

        self._resource_repo.update_by_id(resource_id, {"status": "inactive"})
        logger.info("자원 비활성화: %s", resource_id)
        return {"resource_id": resource_id, "status": "inactive"}
