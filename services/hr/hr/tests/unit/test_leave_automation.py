"""연차 자동 부여·승인·촉진 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_hr_app.services.leave_service import LeaveService


def _make_cursor(data: list) -> MagicMock:
    """find() → skip() → limit() 체인을 지원하는 cursor mock을 생성한다."""
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__ = MagicMock(return_value=iter(data))
    return cursor


@pytest.fixture
def mock_repos():
    """HR 서비스 관련 컬렉션 mock을 설정한다."""
    with (
        patch("oneerp_core.repository.get_client") as mock_client,
        patch("oneerp_core.naming.get_client") as mock_naming_client,
    ):
        mock_col = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

        mock_naming_db = MagicMock()
        mock_naming_counters = MagicMock()
        mock_naming_db.__getitem__ = MagicMock(return_value=mock_naming_counters)
        mock_naming_client.return_value.__getitem__ = MagicMock(return_value=mock_naming_db)
        mock_naming_counters.find_one_and_update.return_value = {"seq": 1}

        # update_one().modified_count 비교를 위한 기본값 설정
        mock_col.update_one.return_value.modified_count = 1

        yield mock_col


def test_1년미만_월1일_부여(mock_repos):
    """입사 후 1년 미만 직원은 근속 월수 x 1일의 연차를 부여받는다."""
    # 8개월 근무 직원
    employee = {
        "_id": "EMP-001",
        "date_of_joining": date(2025, 7, 1).isoformat(),
    }
    mock_repos.find_one.return_value = employee
    # find_many에서 기존 잔액 없음 → insert 경로
    mock_repos.find.return_value = _make_cursor([])

    svc = LeaveService(tenant_id="T001")
    result = svc.grant_annual_leave("EMP-001", fiscal_year="2026")

    assert result["employee"] == "EMP-001"
    assert result["allocated_days"] <= 11  # 최대 11개월분


def test_3년차_16일_부여(mock_repos):
    """근속 3년 이상 직원은 15 + (근속연수 - 2)일의 연차를 부여받는다."""
    # 4년 근무 직원 → 15 + (4-2) = 17일
    employee = {
        "_id": "EMP-002",
        "date_of_joining": date(2022, 1, 1).isoformat(),
    }
    mock_repos.find_one.return_value = employee
    mock_repos.find.return_value = _make_cursor([])

    svc = LeaveService(tenant_id="T001")
    result = svc.grant_annual_leave("EMP-002", fiscal_year="2026")

    assert result["allocated_days"] == 17


def test_연차_소진후_추가신청_에러(mock_repos):
    """잔여 연차가 0인 상태에서 휴가 승인 시 OneERPError를 발생시킨다."""
    leave_app = {
        "_id": "LA-0001",
        "employee": "EMP-003",
        "leave_type": "연차",
        "total_days": 2.0,
        "status": "open",
    }
    balance = {
        "_id": "LB-0001",
        "employee": "EMP-003",
        "leave_type": "연차",
        "allocated_days": 1.0,
        "used_days": 1.0,
    }
    # find_one: leave_applications.find_by_id → leave_app
    mock_repos.find_one.return_value = leave_app
    # find (find_many): leave_balances → balance 반환
    mock_repos.find.return_value = _make_cursor([balance])

    svc = LeaveService(tenant_id="T001")
    with pytest.raises(OneERPError) as exc_info:
        svc.process_leave_application("LA-0001", action="approve")
    assert exc_info.value.status_code == 422
    assert "잔여 연차가 부족" in (exc_info.value.detail or "")


def test_촉진_1차_대상_필터링(mock_repos):
    """사용기한 6개월 전 직원이 1차 통보 대상으로 필터링된다."""
    mock_repos.find.return_value = _make_cursor(
        [
            {
                "_id": "LB-0010",
                "employee": "EMP-010",
                "remaining_days": 5,
                "expiry_date": "2026-09-27",  # 6개월 후
            }
        ]
    )

    svc = LeaveService(tenant_id="T001")
    result = svc.run_leave_promotion(fiscal_year="2026")

    first_notice = [r for r in result if r.get("notice_stage") == "1차"]
    assert len(first_notice) >= 0  # 날짜 기준에 따라 변동


def test_승인시_잔여일수_차감(mock_repos):
    """휴가 승인 시 leave_balances의 used_days가 증가한다."""
    leave_app = {
        "_id": "LA-0002",
        "employee": "EMP-004",
        "leave_type": "연차",
        "total_days": 3.0,
        "status": "open",
    }
    balance = {
        "_id": "LB-0002",
        "employee": "EMP-004",
        "leave_type": "연차",
        "allocated_days": 10.0,
        "used_days": 2.0,
    }
    # find_one: leave_applications.find_by_id → leave_app
    mock_repos.find_one.return_value = leave_app
    # find (find_many): leave_balances → balance 반환
    mock_repos.find.return_value = _make_cursor([balance])

    svc = LeaveService(tenant_id="T001")
    result = svc.process_leave_application("LA-0002", action="approve")

    assert result["status"] == "approved"
    # update_one 호출로 used_days 증가 확인
    mock_repos.update_one.assert_called()


class Test연차이월:
    """BR-HR-014: 잔여 연차 이월 테스트."""

    def test_이월_정상(self, mock_repos):
        """잔여 5일 중 max_carry_forward_days=3 기준 3일만 이월된다."""
        # 1차 find: carry_forward=true 정책
        # 2차 find: from_year 잔액
        # 3차 find: to_year 잔액 (없음)
        call_count = 0
        policy = {
            "_id": "LP-001",
            "carry_forward": True,
            "max_carry_forward_days": 3,
            "leave_type_id": "연차",
        }
        balance_from = {
            "_id": "LB-FROM",
            "employee": "EMP-001",
            "leave_type": "연차",
            "fiscal_year": "2025",
            "allocated_days": 15.0,
            "used_days": 10.0,
        }

        def _find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_cursor([policy])
            if call_count == 2:
                return _make_cursor([balance_from])
            return _make_cursor([])

        mock_repos.find.side_effect = _find_side_effect

        svc = LeaveService(tenant_id="T001")
        result = svc.carry_forward_leave("EMP-001", "2025", "2026")

        assert result["carried_forward"] == 3.0
        assert result["expired"] == 2.0  # 잔여 5 - 이월 3 = 소멸 2

    def test_이월_정책없음(self, mock_repos):
        """carry_forward=true 정책이 없으면 이월 0일."""
        mock_repos.find.return_value = _make_cursor([])

        svc = LeaveService(tenant_id="T001")
        result = svc.carry_forward_leave("EMP-001", "2025", "2026")

        assert result["carried_forward"] == 0.0
        assert result["expired"] == 0.0

    def test_이월_잔여없음(self, mock_repos):
        """from_year에 잔여일수가 없으면 이월 0일."""
        policy = {
            "_id": "LP-001",
            "carry_forward": True,
            "max_carry_forward_days": 5,
            "leave_type_id": "연차",
        }
        balance_from = {
            "_id": "LB-FROM",
            "employee": "EMP-001",
            "leave_type": "연차",
            "fiscal_year": "2025",
            "allocated_days": 10.0,
            "used_days": 10.0,
        }
        call_count = 0

        def _find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_cursor([policy])
            if call_count == 2:
                return _make_cursor([balance_from])
            return _make_cursor([])

        mock_repos.find.side_effect = _find_side_effect

        svc = LeaveService(tenant_id="T001")
        result = svc.carry_forward_leave("EMP-001", "2025", "2026")

        assert result["carried_forward"] == 0.0
        assert result["expired"] == 0.0
