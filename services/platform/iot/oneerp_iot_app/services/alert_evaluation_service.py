"""IoT 알림 평가 서비스 — 데이터 포인트 기반 알림 규칙 평가."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

_OPERATORS: dict[str, Any] = {
    ">": Decimal.__gt__,
    ">=": Decimal.__ge__,
    "<": Decimal.__lt__,
    "<=": Decimal.__le__,
    "==": Decimal.__eq__,
}


def evaluate_alert_rules(
    value: Decimal,
    alert_rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """데이터 포인트 값을 알림 규칙과 비교하여 트리거된 알림 목록을 반환한다.

    Args:
        value: 측정값.
        alert_rules: 알림 규칙 목록 (metric, operator, threshold).

    Returns:
        트리거된 알림 규칙 목록.
    """
    triggered: list[dict[str, Any]] = []
    for rule in alert_rules:
        threshold = Decimal(str(rule.get("threshold", 0)))
        operator = rule.get("operator", "")
        cmp_fn = _OPERATORS.get(operator)
        if cmp_fn and cmp_fn(value, threshold):
            triggered.append(rule)

    return triggered
