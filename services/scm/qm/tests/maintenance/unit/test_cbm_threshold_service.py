"""CBM(상태기반보전) 임계값 평가 서비스 단위 테스트.

BR-MNT-019: 센서 데이터 수신 시 활성 CBM 규칙과 매칭 (연산자별 임계값 비교)
BR-MNT-020: consecutive_count > 1인 규칙은 연속 N회 초과 시에만 트리거 (노이즈 필터링)
BR-MNT-021: cooldown_minutes 이내 재트리거 방지
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _make_service():
    """서비스 + mock repo."""
    with patch(
        "oneerp_qm_app.maintenance.services.cbm_threshold_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _factory
        from oneerp_qm_app.maintenance.services.cbm_threshold_service import CBMThresholdService

        svc = CBMThresholdService(tenant_id="T1")
    return svc, repos


class TestOperatorEvaluation:
    """BR-MNT-019 — 임계값 비교 연산자 테스트."""

    def test_gt_초과(self) -> None:
        """gt: value > threshold."""
        svc, _ = _make_service()
        assert svc.evaluate_condition(value=10.5, operator="gt", threshold=10.0) is True
        assert svc.evaluate_condition(value=10.0, operator="gt", threshold=10.0) is False

    def test_gte_이상(self) -> None:
        """gte: value >= threshold."""
        svc, _ = _make_service()
        assert svc.evaluate_condition(value=10.0, operator="gte", threshold=10.0) is True
        assert svc.evaluate_condition(value=9.9, operator="gte", threshold=10.0) is False

    def test_lt_미만(self) -> None:
        """lt: value < threshold."""
        svc, _ = _make_service()
        assert svc.evaluate_condition(value=5.0, operator="lt", threshold=10.0) is True
        assert svc.evaluate_condition(value=10.0, operator="lt", threshold=10.0) is False

    def test_between_범위(self) -> None:
        """between: lower <= value <= upper."""
        svc, _ = _make_service()
        assert (
            svc.evaluate_condition(
                value=7.0,
                operator="between",
                threshold=5.0,
                threshold_upper=10.0,
            )
            is True
        )
        assert (
            svc.evaluate_condition(
                value=11.0,
                operator="between",
                threshold=5.0,
                threshold_upper=10.0,
            )
            is False
        )

    def test_알수없는_연산자는_에러(self) -> None:
        svc, _ = _make_service()
        with pytest.raises(ValueError, match="연산자"):
            svc.evaluate_condition(value=1.0, operator="xyz", threshold=1.0)


class TestRuleMatching:
    """BR-MNT-019 — 센서 데이터와 활성 CBM 규칙 매칭 테스트."""

    def test_활성_규칙만_평가(self) -> None:
        """is_active=False 규칙은 평가 대상에서 제외."""
        svc, repos = _make_service()
        repos["cbm_rules"].find_many.return_value = [
            {
                "_id": "RULE-1",
                "equipment_id": "EQ-001",
                "meter_type": "vibration",
                "operator": "gt",
                "threshold": 5.0,
                "consecutive_count": 1,
                "cooldown_minutes": 0,
                "is_active": True,
            },
            {
                "_id": "RULE-2",
                "equipment_id": "EQ-001",
                "meter_type": "vibration",
                "operator": "gt",
                "threshold": 3.0,
                "consecutive_count": 1,
                "cooldown_minutes": 0,
                "is_active": False,  # 제외됨
            },
        ]

        triggered = svc.process_sensor_reading(
            equipment_id="EQ-001",
            meter_type="vibration",
            value=6.0,
            reading_time=datetime(2026, 4, 10, 10, 0, tzinfo=UTC),
        )

        # RULE-1만 트리거
        assert len(triggered) == 1
        assert triggered[0]["rule_id"] == "RULE-1"

    def test_다른_설비_규칙은_무시(self) -> None:
        """equipment_id가 다른 규칙은 매칭 안 됨."""
        svc, repos = _make_service()
        repos["cbm_rules"].find_many.return_value = []
        # find_many가 filter를 받으므로 호출만 확인
        svc.process_sensor_reading(
            equipment_id="EQ-999",
            meter_type="temperature",
            value=100.0,
            reading_time=datetime(2026, 4, 10, 10, 0, tzinfo=UTC),
        )
        # 호출된 필터에 equipment_id가 포함되어 있어야 함
        call = repos["cbm_rules"].find_many.call_args
        query = call[0][0] if call[0] else call[1].get("query", {})
        assert query.get("equipment_id") == "EQ-999"


class TestConsecutiveFilter:
    """BR-MNT-020 — 연속 N회 초과 필터 테스트."""

    def test_consecutive_1은_즉시_트리거(self) -> None:
        """consecutive_count=1이면 1회 초과로 즉시 트리거."""
        svc, repos = _make_service()
        repos["cbm_rules"].find_many.return_value = [
            {
                "_id": "RULE-1",
                "equipment_id": "EQ-001",
                "meter_type": "vibration",
                "operator": "gt",
                "threshold": 5.0,
                "consecutive_count": 1,
                "cooldown_minutes": 0,
                "is_active": True,
                "current_consecutive": 0,
            },
        ]

        triggered = svc.process_sensor_reading(
            equipment_id="EQ-001",
            meter_type="vibration",
            value=6.0,
            reading_time=datetime(2026, 4, 10, 10, 0, tzinfo=UTC),
        )

        assert len(triggered) == 1

    def test_consecutive_3은_3회_초과_필요(self) -> None:
        """consecutive_count=3이면 3회 연속 초과해야 트리거."""
        svc, repos = _make_service()
        # current_consecutive=2 (이미 2회 연속 초과)
        repos["cbm_rules"].find_many.return_value = [
            {
                "_id": "RULE-1",
                "equipment_id": "EQ-001",
                "meter_type": "vibration",
                "operator": "gt",
                "threshold": 5.0,
                "consecutive_count": 3,
                "cooldown_minutes": 0,
                "is_active": True,
                "current_consecutive": 2,
            },
        ]

        # 3번째 초과 → 트리거
        triggered = svc.process_sensor_reading(
            equipment_id="EQ-001",
            meter_type="vibration",
            value=6.0,
            reading_time=datetime(2026, 4, 10, 10, 0, tzinfo=UTC),
        )
        assert len(triggered) == 1

    def test_조건_미충족시_카운트_리셋(self) -> None:
        """조건 미충족 시 current_consecutive=0으로 리셋."""
        svc, repos = _make_service()
        repos["cbm_rules"].find_many.return_value = [
            {
                "_id": "RULE-1",
                "equipment_id": "EQ-001",
                "meter_type": "vibration",
                "operator": "gt",
                "threshold": 5.0,
                "consecutive_count": 3,
                "cooldown_minutes": 0,
                "is_active": True,
                "current_consecutive": 2,
            },
        ]

        # 미초과 값 → 카운트 리셋, 미트리거
        triggered = svc.process_sensor_reading(
            equipment_id="EQ-001",
            meter_type="vibration",
            value=4.0,
            reading_time=datetime(2026, 4, 10, 10, 0, tzinfo=UTC),
        )
        assert triggered == []
        # update_by_id 호출 시 current_consecutive=0 확인
        update_call = repos["cbm_rules"].update_by_id.call_args
        assert update_call[0][1]["current_consecutive"] == 0


class TestCooldown:
    """BR-MNT-021 — 쿨다운 재트리거 방지 테스트."""

    def test_쿨다운_이내_재트리거_방지(self) -> None:
        """last_triggered_at + cooldown_minutes > now() 시 무시."""
        svc, repos = _make_service()
        now = datetime(2026, 4, 10, 10, 0, tzinfo=UTC)
        # 5분 전에 트리거, 쿨다운 30분
        repos["cbm_rules"].find_many.return_value = [
            {
                "_id": "RULE-1",
                "equipment_id": "EQ-001",
                "meter_type": "vibration",
                "operator": "gt",
                "threshold": 5.0,
                "consecutive_count": 1,
                "cooldown_minutes": 30,
                "is_active": True,
                "last_triggered_at": now - timedelta(minutes=5),
                "current_consecutive": 0,
            },
        ]

        triggered = svc.process_sensor_reading(
            equipment_id="EQ-001",
            meter_type="vibration",
            value=6.0,
            reading_time=now,
        )

        # 쿨다운 중 → 미트리거
        assert triggered == []

    def test_쿨다운_경과후_재트리거_허용(self) -> None:
        """쿨다운이 경과한 이후에는 재트리거 가능."""
        svc, repos = _make_service()
        now = datetime(2026, 4, 10, 10, 0, tzinfo=UTC)
        # 45분 전 트리거, 쿨다운 30분 → 경과 완료
        repos["cbm_rules"].find_many.return_value = [
            {
                "_id": "RULE-1",
                "equipment_id": "EQ-001",
                "meter_type": "vibration",
                "operator": "gt",
                "threshold": 5.0,
                "consecutive_count": 1,
                "cooldown_minutes": 30,
                "is_active": True,
                "last_triggered_at": now - timedelta(minutes=45),
                "current_consecutive": 0,
            },
        ]

        triggered = svc.process_sensor_reading(
            equipment_id="EQ-001",
            meter_type="vibration",
            value=6.0,
            reading_time=now,
        )

        assert len(triggered) == 1
