"""안전 사고 통계 서비스."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class IncidentStatsService:
    """안전 사고 통계 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._incident_repo = Repository("safety_incidents", tenant_id=tenant_id)

    def get_statistics(self) -> dict[str, Any]:
        """안전 사고 통계를 집계한다.

        유형별, 심각도별 사고 건수를 반환한다.
        """
        incidents = self._incident_repo.find_many()

        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_status: dict[str, int] = {}
        kosha_reported = 0

        for incident in incidents:
            # 유형별 집계
            itype = incident.get("incident_type", "unknown")
            by_type[itype] = by_type.get(itype, 0) + 1

            # 심각도별 집계
            severity = incident.get("severity", "unknown")
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # 상태별 집계
            status = incident.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            # 안전공단 신고 건수
            if incident.get("reported_to_kosha"):
                kosha_reported += 1

        logger.info(
            "안전 사고 통계: 전체 %d건, 안전공단 신고 %d건",
            len(incidents),
            kosha_reported,
        )

        return {
            "total_incidents": len(incidents),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_status": by_status,
            "kosha_reported": kosha_reported,
        }
