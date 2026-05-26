"""HolidayService 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """HolidayService + mock 리포지터리를 생성한다."""
    with patch("oneerp_calendar_app.services.holiday_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_calendar_app.services.holiday_service import HolidayService

        service = HolidayService(tenant_id="test-tenant")
    return service, repos


class Test공휴일등록:
    def test_정상_등록(self) -> None:
        service, repos = _make_service()
        repos["holidays"].find_many.return_value = []
        repos["holidays"].insert.return_value = "CHOL-001"

        result = service.register_holiday(
            name="설날",
            holiday_date=date(2026, 1, 29),
            description="음력 1월 1일",
        )

        assert result["name"] == "설날"
        repos["holidays"].insert.assert_called_once()

    def test_중복_날짜_에러(self) -> None:
        service, repos = _make_service()
        repos["holidays"].find_many.return_value = [
            {"_id": "CHOL-001", "name": "기존 공휴일"},
        ]

        with pytest.raises(ValueError, match="ERR-CAL-061"):
            service.register_holiday(
                name="중복 공휴일",
                holiday_date=date(2026, 1, 29),
            )


class Test공휴일확인:
    def test_정확한_날짜_공휴일(self) -> None:
        service, repos = _make_service()
        # find_many 호출: 첫 번째는 정확한 날짜 매칭
        repos["holidays"].find_many.side_effect = [
            [{"_id": "CHOL-001", "holiday_date": "2026-01-01", "name": "신정"}],
        ]

        assert service.is_holiday(date(2026, 1, 1)) is True

    def test_연간_반복_공휴일(self) -> None:
        service, repos = _make_service()
        # 첫 호출: 정확 매칭 없음, 두 번째 호출: 연간 반복 조회
        repos["holidays"].find_many.side_effect = [
            [],  # 정확 매칭
            [
                {
                    "_id": "CHOL-001",
                    "holiday_date": "2025-01-01",
                    "name": "신정",
                    "is_annual": True,
                },
            ],
        ]

        assert service.is_holiday(date(2026, 1, 1)) is True

    def test_공휴일_아닌_날(self) -> None:
        service, repos = _make_service()
        repos["holidays"].find_many.side_effect = [
            [],
            [],
        ]

        assert service.is_holiday(date(2026, 7, 15)) is False


class Test근무일계산:
    def test_주말_제외_계산(self) -> None:
        service, repos = _make_service()
        # is_holiday 호출 시 빈 결과 반환
        repos["holidays"].find_many.return_value = []

        # 2026-03-23(월) ~ 2026-03-27(금): 5 근무일
        result = service.calculate_business_days(
            date(2026, 3, 23),
            date(2026, 3, 27),
        )

        assert result["business_days"] == 5
        assert result["weekends"] == 0
        assert result["total_calendar_days"] == 5

    def test_주말_포함_계산(self) -> None:
        service, repos = _make_service()
        repos["holidays"].find_many.return_value = []

        # 2026-03-23(월) ~ 2026-03-29(일): 5 근무일 + 2 주말
        result = service.calculate_business_days(
            date(2026, 3, 23),
            date(2026, 3, 29),
        )

        assert result["business_days"] == 5
        assert result["weekends"] == 2
        assert result["total_calendar_days"] == 7

    def test_시작일이_종료일보다_늦으면_에러(self) -> None:
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="ERR-CAL-063"):
            service.calculate_business_days(
                date(2026, 3, 29),
                date(2026, 3, 23),
            )


class Test기간별공휴일:
    def test_기간내_공휴일_조회(self) -> None:
        service, repos = _make_service()
        repos["holidays"].find_many.return_value = [
            {
                "_id": "CHOL-001",
                "name": "설날",
                "holiday_date": "2026-01-29",
                "is_annual": False,
            },
            {
                "_id": "CHOL-002",
                "name": "삼일절",
                "holiday_date": "2026-03-01",
                "is_annual": True,
            },
        ]

        result = service.get_holidays_in_range(
            date(2026, 1, 1),
            date(2026, 3, 31),
        )

        # 설날과 삼일절 모두 기간 내
        assert len(result) >= 2

    def test_빈_기간(self) -> None:
        service, repos = _make_service()
        repos["holidays"].find_many.return_value = []

        result = service.get_holidays_in_range(
            date(2026, 7, 1),
            date(2026, 7, 31),
        )

        assert len(result) == 0
