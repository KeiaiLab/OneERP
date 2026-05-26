"""휴가 관리 서비스(LeaveService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError

# Repository 패치를 테스트 실행 중에도 유지하기 위한 컨텍스트 매니저 기반 fixture
_repos: dict[str, MagicMock] = {}
_patcher = None


def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
    """Repository 생성자 mock — 동일 컬렉션명이면 같은 mock 반환."""
    if collection_name not in _repos:
        _repos[collection_name] = MagicMock()
    return _repos[collection_name]


@pytest.fixture(autouse=True)
def _patch_repository():
    """모든 테스트에서 Repository를 mock으로 대체한다."""
    global _patcher
    _repos.clear()
    _patcher = patch("oneerp_hr_app.services.leave_service.Repository", side_effect=_repo_factory)
    _patcher.start()
    yield
    _patcher.stop()


def _make_service():
    from oneerp_hr_app.services.leave_service import LeaveService

    return LeaveService(tenant_id="test-tenant")


class Test휴가잔여:
    def test_잔여일수_계산(self) -> None:
        service = _make_service()
        _repos["leave_balances"].find_many.return_value = [
            {"leave_type": "연차", "allocated_days": 15, "used_days": 5},
            {"leave_type": "병가", "allocated_days": 10, "used_days": 2},
        ]

        result = service.get_leave_balance("EMP-001")

        assert len(result["balances"]) == 2
        assert result["total_remaining"] == 18.0  # (15-5) + (10-2)
        assert result["balances"][0]["remaining"] == 10.0

    def test_특정유형_잔여(self) -> None:
        service = _make_service()
        _repos["leave_balances"].find_many.return_value = [
            {"leave_type": "연차", "allocated_days": 15, "used_days": 5},
        ]

        result = service.get_leave_balance("EMP-001", leave_type="연차")

        assert result["total_remaining"] == 10.0


class Test보상휴가:
    def test_보상휴가_추가(self) -> None:
        service = _make_service()
        _repos["leave_balances"].find_many.return_value = [
            {"_id": "LB-001", "leave_type": "보상휴가", "allocated_days": 2}
        ]

        result = service.process_compensatory_leave("EMP-001", "2026-03-15", "주말근무", 1.0)

        assert result["compensatory_days"] == 1.0
        _repos["leave_balances"].update_by_id.assert_called_once_with(
            "LB-001", {"allocated_days": 3.0}
        )

    def test_보상휴가_신규생성(self) -> None:
        service = _make_service()
        _repos["leave_balances"].find_many.return_value = []

        result = service.process_compensatory_leave("EMP-001", "2026-03-15", "명절근무", 1.5)

        assert result["compensatory_days"] == 1.5
        _repos["leave_balances"].insert.assert_called_once()


class Test휴가승인상태검증:
    """BR-HR-010: OPEN 상태의 휴가 신청만 승인/거절 가능 (이중 승인 방지)."""

    def test_이미_승인된_신청_재승인_시_에러(self) -> None:
        """이미 approved 상태인 휴가 신청을 재승인하면 422 에러가 발생한다."""
        service = _make_service()
        # leave_applications 레포는 메서드 내에서 생성되므로 미리 등록
        _repos["leave_applications"] = MagicMock()
        _repos["leave_applications"].find_by_id.return_value = {
            "_id": "LA-001",
            "employee": "EMP-001",
            "leave_type": "연차",
            "total_days": 3.0,
            "status": "approved",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.process_leave_application("LA-001", action="approve")
        assert exc_info.value.status_code == 422
        assert "OPEN 상태" in (exc_info.value.detail or "")

    def test_거절된_신청_재거절_시_에러(self) -> None:
        """이미 rejected 상태인 휴가 신청을 재거절하면 422 에러가 발생한다."""
        service = _make_service()
        _repos["leave_applications"] = MagicMock()
        _repos["leave_applications"].find_by_id.return_value = {
            "_id": "LA-002",
            "employee": "EMP-001",
            "status": "rejected",
        }

        with pytest.raises(OneERPError) as exc_info:
            service.process_leave_application("LA-002", action="reject")
        assert exc_info.value.status_code == 422

    def test_open_상태_승인_정상처리(self) -> None:
        """open 상태의 휴가 신청은 정상적으로 승인된다."""
        service = _make_service()
        _repos["leave_applications"] = MagicMock()
        _repos["leave_applications"].find_by_id.return_value = {
            "_id": "LA-003",
            "employee": "EMP-001",
            "leave_type": "연차",
            "total_days": 2.0,
            "status": "open",
        }
        _repos["leave_balances"].find_many.return_value = [
            {
                "_id": "LB-001",
                "allocated_days": 15.0,
                "used_days": 3.0,
            }
        ]

        result = service.process_leave_application("LA-003", action="approve")

        assert result["status"] == "approved"


class Test연차촉진쿼리:
    """BR-HR-004: run_leave_promotion의 쿼리가 올바른 필드를 참조하는지 검증."""

    def test_잔여일수_0인_직원_제외(self) -> None:
        """allocated_days == used_days인 직원은 촉진 대상에서 제외된다."""
        service = _make_service()
        # leave_promotion_notices 레포는 메서드 내에서 생성되므로 미리 등록
        _repos["leave_promotion_notices"] = MagicMock()
        _repos["leave_balances"].find_many.return_value = [
            {
                "_id": "LB-010",
                "employee": "EMP-010",
                "allocated_days": 15.0,
                "used_days": 15.0,
                "expiry_date": "2026-09-27",
            },
        ]

        result = service.run_leave_promotion(fiscal_year="2026")

        assert len(result) == 0

    def test_잔여일수_양수_직원_촉진대상(self) -> None:
        """잔여 일수가 있고 만기일이 6개월 이내인 직원은 촉진 대상이다."""
        service = _make_service()
        _repos["leave_promotion_notices"] = MagicMock()
        from datetime import UTC, datetime, timedelta

        expiry = datetime.now(UTC).date() + timedelta(days=170)
        _repos["leave_balances"].find_many.return_value = [
            {
                "_id": "LB-011",
                "employee": "EMP-011",
                "leave_type": "연차",
                "allocated_days": 15.0,
                "used_days": 5.0,
                "expiry_date": expiry.isoformat(),
            },
        ]

        result = service.run_leave_promotion(fiscal_year="2026")

        assert len(result) == 1
        assert result[0]["notice_stage"] == "1차"
        assert result[0]["remaining_days"] == 10.0
