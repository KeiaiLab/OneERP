"""MTBF/MTTR/OEE/가동률 분석 서비스 — CMMS 핵심 KPI 산출.

BR-MNT-022: MTBF = 총 가동 시간 / 고장 횟수 (고장 0건 시 총 가동 시간 반환)
BR-MNT-023: MTTR = 총 수리 시간 / 수리 건수 (수리 0건 시 0 반환)
BR-MNT-024: OEE = 가용률 x 성능률 x 품질률 (각 요소 0~1 클램핑)
BR-MNT-025: 가동률 = (가용 - 정지) / 가용 (소수점 4자리)

참고:
- MTBF는 severity critical/major 고장만 포함 (경미한 이상은 제외)
- MTTR은 maintenance_type=corrective, status=closed인 WO의 실 작업시간만 집계
- OEE world-class 기준 85% (ASQ/SMRP)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from oneerp_core.repository import Repository

if TYPE_CHECKING:
    from datetime import datetime

logger = logging.getLogger(__name__)

# MTBF 산출에 포함되는 고장 severity
_VALID_FAILURE_SEVERITIES: frozenset[str] = frozenset({"critical", "major"})


class MTBFMTTRAnalysisService:
    """설비 신뢰성 KPI(MTBF/MTTR/가동률/OEE) 분석 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._fr_repo = Repository("breakdown_reports", tenant_id=tenant_id)
        self._wo_repo = Repository("work_orders", tenant_id=tenant_id)

    def compute_mtbf(
        self,
        *,
        equipment_id: str,
        period_start: datetime,
        period_end: datetime,
        total_downtime_hours: float,
    ) -> dict[str, Any]:
        """MTBF(평균 고장 간격) 시간(h) 산출.

        MTBF = (총 가용 시간 - 총 정지 시간) / 유효 고장 건수
        유효 고장 = severity in {critical, major}

        Args:
            equipment_id: 설비 ID
            period_start: 기간 시작
            period_end: 기간 종료
            total_downtime_hours: 총 정지 시간(h) — 외부 투입

        Returns:
            {mtbf_hours, failure_count, uptime_hours}
        """
        total_seconds = (period_end - period_start).total_seconds()
        total_hours = total_seconds / 3600.0
        uptime_hours = max(total_hours - total_downtime_hours, 0.0)

        # 기간 내 고장 이력 조회
        failures = self._fr_repo.find_many(
            {
                "equipment_id": equipment_id,
                "failure_datetime": {"$gte": period_start, "$lte": period_end},
            },
            limit=10000,
        )
        valid_failures = [f for f in failures if f.get("severity") in _VALID_FAILURE_SEVERITIES]
        failure_count = len(valid_failures)

        # BR-MNT-022: 고장 0건이면 uptime_hours 그대로, 아니면 평균
        mtbf_hours = uptime_hours if failure_count == 0 else uptime_hours / failure_count
        mtbf_hours = round(mtbf_hours, 4)

        logger.info(
            "MTBF 산출: 설비=%s, 기간=%s~%s, 가동=%.2fh, 고장=%d건 → MTBF=%.2fh",
            equipment_id,
            period_start.date(),
            period_end.date(),
            uptime_hours,
            failure_count,
            mtbf_hours,
        )

        return {
            "equipment_id": equipment_id,
            "mtbf_hours": mtbf_hours,
            "failure_count": failure_count,
            "uptime_hours": round(uptime_hours, 4),
        }

    def compute_mttr(
        self,
        *,
        equipment_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """MTTR(평균 수리 시간) 시간(h) 산출.

        MTTR = SUM(actual_end - actual_start) / 완료된 수리 WO 건수
        대상: maintenance_type=corrective, status=closed, actual_end_date 존재

        Args:
            equipment_id: 설비 ID
            period_start: 기간 시작
            period_end: 기간 종료

        Returns:
            {mtbf_hours, repair_count, total_repair_hours}
        """
        work_orders = self._wo_repo.find_many(
            {
                "equipment_id": equipment_id,
                "maintenance_type": "corrective",
                "actual_end_date": {"$gte": period_start, "$lte": period_end},
            },
            limit=10000,
        )

        total_repair_seconds = 0.0
        repair_count = 0
        for wo in work_orders:
            if wo.get("status") != "closed":
                continue
            start = wo.get("actual_start_date")
            end = wo.get("actual_end_date")
            if not start or not end:
                continue
            duration = (end - start).total_seconds()
            if duration <= 0:
                continue
            total_repair_seconds += duration
            repair_count += 1

        total_repair_hours = total_repair_seconds / 3600.0

        # BR-MNT-023: 수리 0건 시 0 반환
        mttr_hours = 0.0 if repair_count == 0 else total_repair_hours / repair_count

        logger.info(
            "MTTR 산출: 설비=%s, 수리=%d건, 총=%.2fh → MTTR=%.2fh",
            equipment_id,
            repair_count,
            total_repair_hours,
            mttr_hours,
        )

        return {
            "equipment_id": equipment_id,
            "mttr_hours": round(mttr_hours, 4),
            "repair_count": repair_count,
            "total_repair_hours": round(total_repair_hours, 4),
        }

    def compute_availability(
        self,
        total_available_hours: float,
        total_downtime_hours: float,
    ) -> float:
        """가동률 산출.

        BR-MNT-025: 가동률 = (가용 - 정지) / 가용

        Args:
            total_available_hours: 총 가용 시간(h)
            total_downtime_hours: 총 정지 시간(h)

        Returns:
            가동률 (0~1.0, 소수점 4자리)
        """
        if total_available_hours <= 0:
            msg = "가용 시간은 0보다 커야 합니다"
            raise ValueError(msg)

        availability = (total_available_hours - total_downtime_hours) / total_available_hours
        # 0~1 범위 클램핑 (과거 데이터 오류로 음수가 나올 수 있음)
        availability = max(0.0, min(1.0, availability))
        return round(availability, 4)

    def compute_oee(
        self,
        *,
        availability: float,
        performance: float,
        quality: float,
    ) -> float:
        """OEE(설비종합효율) 산출.

        BR-MNT-024: OEE = 가용률 x 성능률 x 품질률
        각 요소를 0~1 범위로 클램핑한다.

        Args:
            availability: 가용률
            performance: 성능률
            quality: 품질률

        Returns:
            OEE (0~1, 소수점 4자리)
        """

        def _clamp(x: float) -> float:
            return max(0.0, min(1.0, x))

        a = _clamp(availability)
        p = _clamp(performance)
        q = _clamp(quality)
        oee = round(a * p * q, 4)

        logger.debug(
            "OEE 산출: A=%.4f, P=%.4f, Q=%.4f → OEE=%.4f",
            a,
            p,
            q,
            oee,
        )
        return oee
