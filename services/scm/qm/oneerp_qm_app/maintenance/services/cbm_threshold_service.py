"""CBM(상태기반보전) 임계값 평가 서비스 — 센서 데이터 기반 예측 보전.

BR-MNT-019: 센서 데이터 수신 시 활성 CBM 규칙과 매칭 (gt/gte/lt/lte/eq/between)
BR-MNT-020: consecutive_count > 1 시 연속 N회 초과해야만 트리거 (노이즈 필터링)
BR-MNT-021: cooldown_minutes 이내 재트리거 방지 (last_triggered_at 기준)

센서 데이터 처리 흐름:
  1. 해당 설비 + 해당 meter_type의 활성 CBM 규칙 조회
  2. 각 규칙에 대해 operator/threshold로 조건 평가
  3. 조건 충족 → current_consecutive 증가, 미충족 → 0으로 리셋
  4. current_consecutive >= consecutive_count AND 쿨다운 경과 → 트리거
  5. 트리거 결과 반환 (상위 워크플로우에서 WO 생성 / 알림 등 수행)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 지원되는 비교 연산자 집합
_SUPPORTED_OPERATORS: frozenset[str] = frozenset(
    {"gt", "gte", "lt", "lte", "eq", "between"},
)


class CBMThresholdService:
    """CBM 임계값 평가 및 트리거 관리 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._rules_repo = Repository("cbm_rules", tenant_id=tenant_id)

    def evaluate_condition(
        self,
        *,
        value: float,
        operator: str,
        threshold: float,
        threshold_upper: float | None = None,
    ) -> bool:
        """단일 조건의 임계값 비교를 평가한다.

        Args:
            value: 측정값
            operator: gt/gte/lt/lte/eq/between
            threshold: 기준 임계값 (between 연산자일 때는 lower bound)
            threshold_upper: between 연산자의 upper bound

        Returns:
            조건 충족 여부

        Raises:
            ValueError: 지원되지 않는 연산자
        """
        if operator not in _SUPPORTED_OPERATORS:
            msg = f"지원되지 않는 연산자: {operator}"
            raise ValueError(msg)

        if operator == "gt":
            return value > threshold
        if operator == "gte":
            return value >= threshold
        if operator == "lt":
            return value < threshold
        if operator == "lte":
            return value <= threshold
        if operator == "eq":
            return value == threshold
        # between
        upper = threshold_upper if threshold_upper is not None else threshold
        return threshold <= value <= upper

    def process_sensor_reading(
        self,
        *,
        equipment_id: str,
        meter_type: str,
        value: float,
        reading_time: datetime,
    ) -> list[dict[str, Any]]:
        """센서 데이터 1건을 받아 적용 가능한 활성 CBM 규칙을 평가하고 트리거한다.

        Args:
            equipment_id: 설비 ID
            meter_type: 계측 유형 (vibration, temperature, operating_hours 등)
            value: 측정값
            reading_time: 측정 시각

        Returns:
            트리거된 규칙 목록 — 각 원소에 rule_id, equipment_id, value, triggered_at 포함
        """
        # 활성 + 동일 설비/계측 유형 규칙만 조회
        rules = self._rules_repo.find_many(
            {
                "equipment_id": equipment_id,
                "meter_type": meter_type,
                "is_active": True,
            },
            limit=500,
        )

        triggered: list[dict[str, Any]] = []

        for rule in rules:
            # 안전장치: 호출자가 is_active=True 필터를 걸었지만 방어적으로 재확인
            if not rule.get("is_active", False):
                continue
            rule_id = rule.get("_id", "")
            operator = rule.get("operator", "gt")
            threshold = float(rule.get("threshold", 0.0))
            threshold_upper = rule.get("threshold_upper")
            if threshold_upper is not None:
                threshold_upper = float(threshold_upper)

            consecutive_required = int(rule.get("consecutive_count", 1))
            cooldown_minutes = int(rule.get("cooldown_minutes", 0))
            current_consecutive = int(rule.get("current_consecutive", 0))
            last_triggered_at = rule.get("last_triggered_at")

            # 1) 조건 평가
            condition_met = self.evaluate_condition(
                value=value,
                operator=operator,
                threshold=threshold,
                threshold_upper=threshold_upper,
            )

            if not condition_met:
                # 미충족 → 카운트 리셋 (BR-MNT-020 노이즈 필터 보조)
                if current_consecutive > 0:
                    self._rules_repo.update_by_id(
                        rule_id,
                        {"current_consecutive": 0},
                    )
                continue

            # 2) 연속 카운트 증가
            new_consecutive = current_consecutive + 1

            # 3) BR-MNT-020: 연속 N회 미만이면 카운트만 증가 후 종료
            if new_consecutive < consecutive_required:
                self._rules_repo.update_by_id(
                    rule_id,
                    {"current_consecutive": new_consecutive},
                )
                logger.debug(
                    "CBM 연속 카운트 증가: rule=%s, %d/%d",
                    rule_id,
                    new_consecutive,
                    consecutive_required,
                )
                continue

            # 4) BR-MNT-021: 쿨다운 확인
            if (
                last_triggered_at is not None
                and cooldown_minutes > 0
                and reading_time - last_triggered_at < timedelta(minutes=cooldown_minutes)
            ):
                logger.info(
                    "CBM 쿨다운 중: rule=%s, 마지막 트리거=%s",
                    rule_id,
                    last_triggered_at,
                )
                # 쿨다운 중이지만 연속 카운트는 유지 (현재 카운트로 기록)
                self._rules_repo.update_by_id(
                    rule_id,
                    {"current_consecutive": new_consecutive},
                )
                continue

            # 5) 트리거 — 카운트 리셋 + last_triggered_at 갱신
            self._rules_repo.update_by_id(
                rule_id,
                {
                    "current_consecutive": 0,
                    "last_triggered_at": reading_time,
                    "last_triggered_value": value,
                },
            )

            triggered.append(
                {
                    "rule_id": rule_id,
                    "equipment_id": equipment_id,
                    "meter_type": meter_type,
                    "value": value,
                    "threshold": threshold,
                    "operator": operator,
                    "action_type": rule.get("action_type", "create_wo"),
                    "triggered_at": reading_time,
                },
            )

            logger.info(
                "CBM 트리거: rule=%s, 설비=%s, %s %s %s (측정=%s)",
                rule_id,
                equipment_id,
                meter_type,
                operator,
                threshold,
                value,
            )

        return triggered
