"""매출 예측 서비스 단위 테스트.

BR-CRM-021: 가중 파이프라인 매출 예측
BR-CRM-022: forecast 카테고리 분류 (Commit/Best Case/Pipeline)
BR-CRM-023: 단계별 정체 시간 기반 확률 감쇠
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from oneerp_crm_app.services.forecast_service import ForecastService


@pytest.fixture
def service():
    """ForecastService 인스턴스와 mock repository를 반환한다."""
    svc = ForecastService.__new__(ForecastService)
    svc._tenant_id = "test-tenant"
    svc._opp_repo = MagicMock()
    return svc


class Test가중기대값계산:
    """BR-CRM-021: 단일 기회의 가중 기대값 산출."""

    def test_기본_가중값_계산(self, service) -> None:
        """weighted_value = amount x probability / 100."""
        result = service.calculate_weighted_value(
            expected_amount=Decimal(10000000),
            probability=Decimal(60),
        )

        assert result["weighted_value"] == 6000000.0
        assert result["adjusted_probability"] == 60.0
        assert result["stalled"] is False

    def test_0_확률은_0_가중값(self, service) -> None:
        result = service.calculate_weighted_value(
            expected_amount=Decimal(5000000),
            probability=Decimal(0),
        )

        assert result["weighted_value"] == 0.0

    def test_100_확률은_전액(self, service) -> None:
        result = service.calculate_weighted_value(
            expected_amount=Decimal(3000000),
            probability=Decimal(100),
        )

        assert result["weighted_value"] == 3000000.0


class Test정체확률감쇠:
    """BR-CRM-023: stalled deal 확률 감쇠."""

    def test_close_date_경과_시_감쇠(self, service) -> None:
        """close_date가 과거면 probability x 0.7."""
        past_date = datetime.now(tz=UTC).date() - timedelta(days=10)

        result = service.calculate_weighted_value(
            expected_amount=Decimal(10000000),
            probability=Decimal(80),
            close_date=past_date,
        )

        # 80 x 0.7 = 56
        assert result["stalled"] is True
        assert result["adjusted_probability"] == 56.0
        assert result["weighted_value"] == 5600000.0

    def test_45일_초과_단계_체류_감쇠(self, service) -> None:
        """stage_entered_at이 45일 초과면 감쇠."""
        long_ago = datetime.now(tz=UTC) - timedelta(days=60)

        result = service.calculate_weighted_value(
            expected_amount=Decimal(5000000),
            probability=Decimal(50),
            stage_entered_at=long_ago,
        )

        # 50 x 0.7 = 35
        assert result["stalled"] is True
        assert result["adjusted_probability"] == 35.0

    def test_30일_체류는_감쇠없음(self, service) -> None:
        """45일 이내 체류는 정상."""
        recent = datetime.now(tz=UTC) - timedelta(days=30)

        result = service.calculate_weighted_value(
            expected_amount=Decimal(5000000),
            probability=Decimal(50),
            stage_entered_at=recent,
        )

        assert result["stalled"] is False
        assert result["adjusted_probability"] == 50.0


class TestForecast카테고리분류:
    """BR-CRM-022: Commit/Best Case/Pipeline 분류."""

    def test_90퍼센트_이상은_commit(self, service) -> None:
        assert service._categorize(Decimal(90)) == "commit"
        assert service._categorize(Decimal(95)) == "commit"
        assert service._categorize(Decimal(100)) == "commit"

    def test_60_89퍼센트는_best_case(self, service) -> None:
        assert service._categorize(Decimal(60)) == "best_case"
        assert service._categorize(Decimal(75)) == "best_case"
        assert service._categorize(Decimal(89)) == "best_case"

    def test_1_59퍼센트는_pipeline(self, service) -> None:
        assert service._categorize(Decimal(1)) == "pipeline"
        assert service._categorize(Decimal(30)) == "pipeline"
        assert service._categorize(Decimal(59)) == "pipeline"

    def test_0퍼센트는_omitted(self, service) -> None:
        assert service._categorize(Decimal(0)) == "omitted"


class TestForecast요약집계:
    """BR-CRM-021/022: 기간별 forecast 요약."""

    def test_빈_파이프라인은_0_반환(self, service) -> None:
        service._opp_repo.find_many.return_value = []

        result = service.get_forecast_summary()

        assert result["deal_count"] == 0
        assert result["weighted_total"] == 0.0
        assert result["commit"] == 0.0
        assert result["best_case"] == 0.0
        assert result["pipeline"] == 0.0

    def test_3건의_카테고리별_집계(self, service) -> None:
        """각 카테고리에 1건씩 배치하여 집계 검증."""
        service._opp_repo.find_many.return_value = [
            # Commit: 95% x 1000만 = 950만
            {
                "_id": "OPP-1",
                "expected_amount": 10000000,
                "probability": 95,
                "status": "open",
            },
            # Best Case: 70% x 2000만 = 1400만
            {
                "_id": "OPP-2",
                "expected_amount": 20000000,
                "probability": 70,
                "status": "open",
            },
            # Pipeline: 30% x 500만 = 150만
            {
                "_id": "OPP-3",
                "expected_amount": 5000000,
                "probability": 30,
                "status": "quotation",
            },
        ]

        result = service.get_forecast_summary()

        assert result["deal_count"] == 3
        assert result["total_open_amount"] == 35000000.0
        assert result["commit"] == 9500000.0
        assert result["best_case"] == 14000000.0
        assert result["pipeline"] == 1500000.0
        assert result["weighted_total"] == 25000000.0  # 총합
        assert result["stalled_count"] == 0

    def test_정체_건_카운트(self, service) -> None:
        """stalled deal을 카운트한다."""
        past_close = (datetime.now(tz=UTC).date() - timedelta(days=15)).isoformat()
        service._opp_repo.find_many.return_value = [
            {
                "_id": "OPP-STALL",
                "expected_amount": 1000000,
                "probability": 80,
                "status": "open",
                "close_date": past_close,
            }
        ]

        result = service.get_forecast_summary()

        assert result["stalled_count"] == 1
        # 80 x 0.7 = 56 -> 1000000 x 0.56 = 560000
        assert result["weighted_total"] == 560000.0


class Test파이프라인속도:
    """Pipeline Velocity 지표."""

    def test_빈_데이터는_0_반환(self, service) -> None:
        service._opp_repo.find_many.return_value = []

        result = service.get_pipeline_velocity()

        assert result["velocity_score"] == 0.0
        assert result["won_count"] == 0
        assert result["win_rate"] == 0.0

    def test_승률_계산(self, service) -> None:
        """10건 중 3건 성사 -> win_rate=30%."""

        # find_many가 status 필터에 따라 다른 결과 반환
        def _find_many(query: dict, limit: int) -> list[dict]:
            if query.get("status") == "won":
                return [
                    {
                        "_id": f"OPP-W-{i}",
                        "expected_amount": 1000000,
                        "status": "won",
                        "created_at": (datetime.now(tz=UTC) - timedelta(days=30)).isoformat(),
                        "updated_at": datetime.now(tz=UTC).isoformat(),
                    }
                    for i in range(3)
                ]
            if query == {}:
                # 전체 10건
                return [{"_id": f"OPP-{i}", "status": "open"} for i in range(7)] + [
                    {
                        "_id": f"OPP-W-{i}",
                        "expected_amount": 1000000,
                        "status": "won",
                        "created_at": (datetime.now(tz=UTC) - timedelta(days=30)).isoformat(),
                        "updated_at": datetime.now(tz=UTC).isoformat(),
                    }
                    for i in range(3)
                ]
            return []

        service._opp_repo.find_many.side_effect = _find_many

        result = service.get_pipeline_velocity()

        assert result["won_count"] == 3
        assert result["win_rate"] == 30.0
        assert result["avg_deal_size"] == 1000000.0
