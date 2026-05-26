"""퇴직금 계산 서비스(RetirementPayService) 단위 테스트.

테스트 시나리오:
- 정상 퇴직금 계산 (3년 근속, 월 300만원)
- 근속기간 1년 미만 → 에러
- 직원 미존재 → 에러
- 급여명세 없음 → 에러
- 경계값: 정확히 365일 근속
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture
def mock_repos():
    """Repository를 mock하여 RetirementPayService를 생성한다."""
    with patch("oneerp_payroll_app.services.retirement_pay_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_payroll_app.services.retirement_pay_service import RetirementPayService

        service = RetirementPayService(tenant_id="test-tenant")

    return service, repos


class Test퇴직금_정상계산:
    """정상 시나리오 퇴직금 계산 테스트."""

    def test_3년_근속_월300만원(self, mock_repos: tuple) -> None:
        """3년 근속, 월 급여 300만원일 때 퇴직금을 정확히 계산한다.

        1일평균임금 = 9,000,000 / 90 = 100,000
        퇴직금 = 100,000 x 30 x (1095/365) = 9,000,000
        """
        service, repos = mock_repos

        # 직원 정보: 2023-01-01 입사
        repos["employees"].find_by_id.return_value = {
            "_id": "EMP-001",
            "date_of_joining": "2023-01-01",
        }

        # 최근 3개월 급여명세: 매월 300만원
        repos["salary_slips"].find_many.return_value = [
            {"gross_pay": 3_000_000, "posting_date": "2025-12-31"},
            {"gross_pay": 3_000_000, "posting_date": "2025-11-30"},
            {"gross_pay": 3_000_000, "posting_date": "2025-10-31"},
        ]

        result = service.calculate("EMP-001", date(2026, 1, 1))

        assert result["employee_id"] == "EMP-001"
        assert result["service_days"] == 1096  # 2023-01-01 ~ 2026-01-01
        assert result["total_gross_3months"] == Decimal(9_000_000)
        assert result["daily_avg_wage"] == Decimal(100_000)
        # 퇴직금 = 100000 * 30 * (1096/365) = 9,008,219 (반올림)
        expected = Decimal(100_000) * Decimal(30) * (Decimal(1096) / Decimal(365))
        expected = expected.quantize(Decimal(1))
        assert result["retirement_amount"] == expected

    def test_경계값_정확히_1년(self, mock_repos: tuple) -> None:
        """근속 정확히 365일이면 퇴직금을 지급한다.

        1일평균임금 = 6,000,000 / 90 = 66,667 (반올림)
        퇴직금 = 66,666.67 * 30 * (365/365) = 2,000,000
        """
        service, repos = mock_repos

        repos["employees"].find_by_id.return_value = {
            "_id": "EMP-002",
            "date_of_joining": date(2025, 3, 29),
        }

        repos["salary_slips"].find_many.return_value = [
            {"gross_pay": 2_000_000, "posting_date": "2026-03-28"},
            {"gross_pay": 2_000_000, "posting_date": "2026-02-28"},
            {"gross_pay": 2_000_000, "posting_date": "2026-01-31"},
        ]

        result = service.calculate("EMP-002", date(2026, 3, 29))

        assert result["service_days"] == 365
        assert result["retirement_amount"] == Decimal(2_000_000)


class Test퇴직금_예외:
    """에러 시나리오 테스트."""

    def test_직원_미존재(self, mock_repos: tuple) -> None:
        """존재하지 않는 직원 ID면 404 에러를 반환한다."""
        service, repos = mock_repos
        repos["employees"].find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.calculate("EMP-NONE", date(2026, 1, 1))
        assert exc_info.value.status_code == 404
        assert "직원을 찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_근속_1년_미만(self, mock_repos: tuple) -> None:
        """근속기간이 1년 미만이면 400 에러를 반환한다."""
        service, repos = mock_repos
        repos["employees"].find_by_id.return_value = {
            "_id": "EMP-003",
            "date_of_joining": "2025-06-01",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.calculate("EMP-003", date(2026, 1, 1))
        assert exc_info.value.status_code == 400
        assert "1년 미만" in (exc_info.value.detail or "")

    def test_급여명세_없음(self, mock_repos: tuple) -> None:
        """급여명세가 없으면 400 에러를 반환한다."""
        service, repos = mock_repos
        repos["employees"].find_by_id.return_value = {
            "_id": "EMP-004",
            "date_of_joining": "2020-01-01",
        }
        repos["salary_slips"].find_many.return_value = []

        with pytest.raises(OneERPError) as exc_info:
            service.calculate("EMP-004", date(2026, 1, 1))
        assert exc_info.value.status_code == 400
        assert "급여명세" in (exc_info.value.detail or "")

    def test_입사일_미설정(self, mock_repos: tuple) -> None:
        """입사일이 없으면 400 에러를 반환한다."""
        service, repos = mock_repos
        repos["employees"].find_by_id.return_value = {
            "_id": "EMP-005",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.calculate("EMP-005", date(2026, 1, 1))
        assert exc_info.value.status_code == 400
        assert "입사일" in (exc_info.value.detail or "")
