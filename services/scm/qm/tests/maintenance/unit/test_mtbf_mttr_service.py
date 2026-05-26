"""MTBF/MTTR/OEE/가동률 분석 서비스 단위 테스트.

BR-MNT-022: MTBF = 총 가동 시간 / 고장 횟수
BR-MNT-023: MTTR = 총 수리 시간 / 수리 건수
BR-MNT-024: OEE = 가용률 x 성능률 x 품질률
BR-MNT-025: 가동률 = (가용 - 정지) / 가용
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest


def _make_service():
    """서비스 + mock repo 인스턴스."""
    with patch("oneerp_qm_app.maintenance.services.mtbf_mttr_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _factory
        from oneerp_qm_app.maintenance.services.mtbf_mttr_service import MTBFMTTRAnalysisService

        svc = MTBFMTTRAnalysisService(tenant_id="T1")
    return svc, repos


def _dt(y: int, m: int, d: int, h: int = 0) -> datetime:
    """datetime 헬퍼."""
    return datetime(y, m, d, h, tzinfo=UTC)


class TestMTBF:
    """BR-MNT-022 — MTBF 산출 테스트."""

    def test_정상_MTBF_계산(self) -> None:
        """총 가동 시간 672h, 고장 4건 → MTBF = 168h."""
        svc, repos = _make_service()
        # 기간 내 severity critical/major 고장 4건
        repos["breakdown_reports"].find_many.return_value = [
            {"_id": "FR-1", "severity": "critical"},
            {"_id": "FR-2", "severity": "major"},
            {"_id": "FR-3", "severity": "critical"},
            {"_id": "FR-4", "severity": "major"},
        ]

        result = svc.compute_mtbf(
            equipment_id="EQ-001",
            period_start=_dt(2026, 1, 1),
            period_end=_dt(2026, 1, 31),  # 30일 = 720h
            total_downtime_hours=48.0,
        )

        # 가동 시간 = 720 - 48 = 672h, MTBF = 672 / 4 = 168h
        assert result["mtbf_hours"] == pytest.approx(168.0, abs=0.01)
        assert result["failure_count"] == 4
        assert result["uptime_hours"] == pytest.approx(672.0, abs=0.01)

    def test_고장_0건이면_총_가동시간_반환(self) -> None:
        """고장 0건일 때는 분모 0 → 총 가동 시간을 그대로 반환."""
        svc, repos = _make_service()
        repos["breakdown_reports"].find_many.return_value = []

        result = svc.compute_mtbf(
            equipment_id="EQ-001",
            period_start=_dt(2026, 1, 1),
            period_end=_dt(2026, 1, 2),  # 24h
            total_downtime_hours=0.0,
        )

        assert result["mtbf_hours"] == pytest.approx(24.0, abs=0.01)
        assert result["failure_count"] == 0

    def test_minor_고장은_제외(self) -> None:
        """severity minor/cosmetic 고장은 MTBF 산출에서 제외."""
        svc, repos = _make_service()
        repos["breakdown_reports"].find_many.return_value = [
            {"_id": "FR-1", "severity": "critical"},
            {"_id": "FR-2", "severity": "minor"},  # 제외
            {"_id": "FR-3", "severity": "cosmetic"},  # 제외
            {"_id": "FR-4", "severity": "major"},
        ]

        result = svc.compute_mtbf(
            equipment_id="EQ-001",
            period_start=_dt(2026, 1, 1),
            period_end=_dt(2026, 1, 11),  # 240h
            total_downtime_hours=10.0,
        )

        # 유효 고장 2건 → MTBF = 230 / 2 = 115h
        assert result["failure_count"] == 2
        assert result["mtbf_hours"] == pytest.approx(115.0, abs=0.01)


class TestMTTR:
    """BR-MNT-023 — MTTR 산출 테스트."""

    def test_정상_MTTR_계산(self) -> None:
        """4건 수리 시간 합 12h → MTTR = 3.0h."""
        svc, repos = _make_service()
        repos["work_orders"].find_many.return_value = [
            {
                "_id": "WO-1",
                "maintenance_type": "corrective",
                "status": "closed",
                "actual_start_date": _dt(2026, 1, 1, 8),
                "actual_end_date": _dt(2026, 1, 1, 11),  # 3h
            },
            {
                "_id": "WO-2",
                "maintenance_type": "corrective",
                "status": "closed",
                "actual_start_date": _dt(2026, 1, 2, 9),
                "actual_end_date": _dt(2026, 1, 2, 11),  # 2h
            },
            {
                "_id": "WO-3",
                "maintenance_type": "corrective",
                "status": "closed",
                "actual_start_date": _dt(2026, 1, 3, 8),
                "actual_end_date": _dt(2026, 1, 3, 13),  # 5h
            },
            {
                "_id": "WO-4",
                "maintenance_type": "corrective",
                "status": "closed",
                "actual_start_date": _dt(2026, 1, 4, 8),
                "actual_end_date": _dt(2026, 1, 4, 10),  # 2h
            },
        ]

        result = svc.compute_mttr(
            equipment_id="EQ-001",
            period_start=_dt(2026, 1, 1),
            period_end=_dt(2026, 1, 31),
        )

        assert result["mttr_hours"] == pytest.approx(3.0, abs=0.01)
        assert result["repair_count"] == 4

    def test_수리_0건이면_0_반환(self) -> None:
        """수리 건수 0건일 때는 0을 반환."""
        svc, repos = _make_service()
        repos["work_orders"].find_many.return_value = []

        result = svc.compute_mttr(
            equipment_id="EQ-001",
            period_start=_dt(2026, 1, 1),
            period_end=_dt(2026, 1, 31),
        )

        assert result["mttr_hours"] == 0.0
        assert result["repair_count"] == 0

    def test_actual_end_date_없는_WO는_제외(self) -> None:
        """actual_end_date 미기입 WO(진행 중)는 MTTR 산출에서 제외."""
        svc, repos = _make_service()
        repos["work_orders"].find_many.return_value = [
            {
                "_id": "WO-1",
                "maintenance_type": "corrective",
                "status": "closed",
                "actual_start_date": _dt(2026, 1, 1, 8),
                "actual_end_date": _dt(2026, 1, 1, 11),  # 3h
            },
            {
                "_id": "WO-2",
                "maintenance_type": "corrective",
                "status": "closed",
                "actual_start_date": _dt(2026, 1, 2, 9),
                "actual_end_date": None,  # 제외
            },
        ]

        result = svc.compute_mttr(
            equipment_id="EQ-001",
            period_start=_dt(2026, 1, 1),
            period_end=_dt(2026, 1, 31),
        )

        assert result["mttr_hours"] == pytest.approx(3.0, abs=0.01)
        assert result["repair_count"] == 1


class TestAvailability:
    """BR-MNT-025 — 가동률 산출 테스트."""

    def test_정상_가동률(self) -> None:
        """가동률 = (720 - 48) / 720 ≈ 0.9333."""
        svc, _ = _make_service()
        result = svc.compute_availability(
            total_available_hours=720.0,
            total_downtime_hours=48.0,
        )
        assert result == pytest.approx(0.9333, abs=1e-3)

    def test_정지시간_0이면_1_0(self) -> None:
        """정지 시간 0 → 가동률 1.0."""
        svc, _ = _make_service()
        assert svc.compute_availability(100.0, 0.0) == pytest.approx(1.0)

    def test_가용시간_0은_에러(self) -> None:
        """가용 시간 0은 0으로 나눗셈 에러."""
        svc, _ = _make_service()
        with pytest.raises(ValueError, match="가용 시간"):
            svc.compute_availability(0.0, 0.0)


class TestOEE:
    """BR-MNT-024 — OEE 산출 테스트."""

    def test_OEE_곱셈(self) -> None:
        """OEE = 0.9 x 0.95 x 0.98 = 0.8379."""
        svc, _ = _make_service()
        result = svc.compute_oee(
            availability=0.9,
            performance=0.95,
            quality=0.98,
        )
        assert result == pytest.approx(0.8379, abs=1e-4)

    def test_각_요소_0_1_범위_클램핑(self) -> None:
        """각 요소가 0~1 범위를 벗어나면 클램핑된다."""
        svc, _ = _make_service()
        # performance 1.2는 1.0으로 클램핑
        result = svc.compute_oee(
            availability=0.9,
            performance=1.2,
            quality=0.98,
        )
        assert result == pytest.approx(0.9 * 1.0 * 0.98, abs=1e-4)

    def test_0_이하_클램핑(self) -> None:
        """음수는 0으로 클램핑되어 OEE=0."""
        svc, _ = _make_service()
        assert svc.compute_oee(availability=0.9, performance=-0.1, quality=0.98) == 0.0
