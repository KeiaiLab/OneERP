"""출장비 일일 정액 서비스(PerDiemService) 단위 테스트 — BR-EXP-NEW-017.

한국 공무원 여비규정을 참조한 국내/해외 출장 일일 정액 계산:
- 국내: 등급별 일비/식비/숙박비 정액
- 해외: 지역 등급(1등급/2등급) x 직급 등급 정액
- 출장 기간 x 정액 = 기본 출장비
- 부분일(0.5일) 처리
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    """PerDiemService와 mock travel repo를 생성한다."""
    with patch("oneerp_expenses_app.services.per_diem_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_expenses_app.services.per_diem_service import PerDiemService

        service = PerDiemService(tenant_id="test-tenant")

    return service, repos["travel_requests"]


class Test국내출장_일일정액:
    """국내 출장 일일 정액 계산."""

    def test_1일_출장_임원등급(self) -> None:
        """1일(당일) 국내 출장 — 임원 등급: 일비 25,000 + 식비 25,000."""
        service, _travel_repo = _make_service()

        result = service.calculate(
            region="domestic",
            grade="executive",
            departure_date=date(2026, 4, 10),
            return_date=date(2026, 4, 10),
        )

        assert result["days"] == Decimal(1)
        assert result["daily_allowance"] == Decimal(25000)
        assert result["meal_allowance"] == Decimal(25000)
        # 당일 출장은 숙박비 없음
        assert result["lodging_allowance"] == Decimal(0)
        assert result["total"] == Decimal(50000)

    def test_2일_1박_출장_일반등급(self) -> None:
        """1박 2일 국내 출장 — 일반 직원: 일비 20,000x2 + 식비 20,000x2 + 숙박 70,000x1."""
        service, _travel_repo = _make_service()

        result = service.calculate(
            region="domestic",
            grade="regular",
            departure_date=date(2026, 4, 10),
            return_date=date(2026, 4, 11),
        )

        assert result["days"] == Decimal(2)
        # 2일 x 일비 20,000 = 40,000
        assert result["daily_allowance"] == Decimal(40000)
        # 2일 x 식비 20,000 = 40,000
        assert result["meal_allowance"] == Decimal(40000)
        # 1박 x 숙박 70,000 = 70,000
        assert result["lodging_allowance"] == Decimal(70000)
        assert result["total"] == Decimal(150000)

    def test_3일_2박_출장_관리직(self) -> None:
        """2박 3일 국내 출장 — 관리직(manager): 일비 22,000 x 3일, 식비 22,000 x 3일, 숙박 80,000 x 2박."""
        service, _travel_repo = _make_service()

        result = service.calculate(
            region="domestic",
            grade="manager",
            departure_date=date(2026, 4, 10),
            return_date=date(2026, 4, 12),
        )

        assert result["days"] == Decimal(3)
        assert result["daily_allowance"] == Decimal(66000)
        assert result["meal_allowance"] == Decimal(66000)
        assert result["lodging_allowance"] == Decimal(160000)
        assert result["total"] == Decimal(292000)


class Test해외출장_일일정액:
    """해외 출장 지역 등급별 일일 정액 계산."""

    def test_1등급지역_미국_임원(self) -> None:
        """1등급 지역(미국/EU) 임원 — 일비 80 USD, 식비 120 USD, 숙박 250 USD."""
        service, _travel_repo = _make_service()

        result = service.calculate(
            region="overseas_tier1",
            grade="executive",
            departure_date=date(2026, 4, 10),
            return_date=date(2026, 4, 12),  # 2박 3일
        )

        assert result["days"] == Decimal(3)
        assert result["currency"] == "USD"
        assert result["daily_allowance"] == Decimal(240)  # 80 x 3
        assert result["meal_allowance"] == Decimal(360)  # 120 x 3
        assert result["lodging_allowance"] == Decimal(500)  # 250 x 2박
        assert result["total"] == Decimal(1100)

    def test_2등급지역_동남아_일반직원(self) -> None:
        """2등급 지역(동남아) 일반 직원 — 일비 40 USD, 식비 60 USD, 숙박 120 USD."""
        service, _travel_repo = _make_service()

        result = service.calculate(
            region="overseas_tier2",
            grade="regular",
            departure_date=date(2026, 4, 10),
            return_date=date(2026, 4, 11),  # 1박 2일
        )

        assert result["days"] == Decimal(2)
        assert result["currency"] == "USD"
        assert result["daily_allowance"] == Decimal(80)  # 40 x 2
        assert result["meal_allowance"] == Decimal(120)  # 60 x 2
        assert result["lodging_allowance"] == Decimal(120)  # 120 x 1박
        assert result["total"] == Decimal(320)


class Test출장정액_검증:
    """유효성 검증 케이스."""

    def test_출발일_귀환일_역전_에러(self) -> None:
        """출발일 > 귀환일이면 422 에러."""
        service, _travel_repo = _make_service()

        with pytest.raises(OneERPError, match="ERR-EXP-032"):
            service.calculate(
                region="domestic",
                grade="regular",
                departure_date=date(2026, 4, 12),
                return_date=date(2026, 4, 10),
            )

    def test_미지원_지역_에러(self) -> None:
        """미지원 지역 코드는 400 에러."""
        service, _travel_repo = _make_service()

        with pytest.raises(OneERPError, match="bad_request"):
            service.calculate(
                region="moon",
                grade="regular",
                departure_date=date(2026, 4, 10),
                return_date=date(2026, 4, 10),
            )

    def test_미지원_등급_에러(self) -> None:
        """미지원 등급은 400 에러."""
        service, _travel_repo = _make_service()

        with pytest.raises(OneERPError, match="bad_request"):
            service.calculate(
                region="domestic",
                grade="ceo_plus",
                departure_date=date(2026, 4, 10),
                return_date=date(2026, 4, 10),
            )


class Test출장신청_정액적용:
    """출장 신청서 기반 정액 계산."""

    def test_travel_request_기반_정액(self) -> None:
        """출장 신청서 ID 기반으로 정액 계산."""
        service, travel_repo = _make_service()
        travel_repo.find_by_id.return_value = {
            "_id": "TR-001",
            "employee_id": "EMP-001",
            "destination": "부산",
            "departure_date": "2026-04-10",
            "return_date": "2026-04-11",
        }

        result = service.calculate_from_request(
            travel_request_id="TR-001",
            region="domestic",
            grade="regular",
        )

        assert result["travel_request_id"] == "TR-001"
        assert result["days"] == Decimal(2)
        # 일반직원 1박 2일: 일비+식비+숙박
        assert result["total"] > Decimal(0)

    def test_travel_request_미존재_404(self) -> None:
        """존재하지 않는 출장 신청 조회 시 404 에러."""
        service, travel_repo = _make_service()
        travel_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.calculate_from_request(
                travel_request_id="TR-999",
                region="domestic",
                grade="regular",
            )
