"""알림 평가 서비스 테스트."""

from __future__ import annotations

from decimal import Decimal

from oneerp_iot_app.services.alert_evaluation_service import evaluate_alert_rules


def test_초과_규칙_트리거() -> None:
    """값이 임계치를 초과하면 알림이 트리거된다."""
    rules = [{"metric": "temperature", "operator": ">", "threshold": 50}]
    result = evaluate_alert_rules(Decimal(55), rules)
    assert len(result) == 1


def test_미만_규칙_트리거() -> None:
    """값이 임계치 미만이면 알림이 트리거된다."""
    rules = [{"metric": "humidity", "operator": "<", "threshold": 20}]
    result = evaluate_alert_rules(Decimal(15), rules)
    assert len(result) == 1


def test_규칙_미해당() -> None:
    """값이 조건을 만족하지 않으면 빈 목록을 반환한다."""
    rules = [{"metric": "temperature", "operator": ">", "threshold": 100}]
    result = evaluate_alert_rules(Decimal(50), rules)
    assert len(result) == 0


def test_다중_규칙_평가() -> None:
    """여러 규칙 중 일부만 트리거된다."""
    rules = [
        {"metric": "temperature", "operator": ">", "threshold": 50},
        {"metric": "temperature", "operator": "<", "threshold": 30},
    ]
    result = evaluate_alert_rules(Decimal(55), rules)
    assert len(result) == 1


def test_같음_규칙_트리거() -> None:
    """값이 임계치와 같으면 == 규칙이 트리거된다."""
    rules = [{"metric": "pressure", "operator": "==", "threshold": 100}]
    result = evaluate_alert_rules(Decimal(100), rules)
    assert len(result) == 1
