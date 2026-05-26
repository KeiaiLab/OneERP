"""구매 승인 매트릭스 서비스(BuyerApprovalService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    with patch("oneerp_buying_app.services.buyer_approval_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_buying_app.services.buyer_approval_service import BuyerApprovalService

        service = BuyerApprovalService(tenant_id="test-tenant")

    return service, repos["buyer_approval_matrices"]


class Test결재자조회:
    """get_approver 테스트."""

    def test_금액_범위_매칭(self) -> None:
        service, matrix_repo = _make_service()
        matrix_repo.find_many.return_value = [
            {
                "_id": "BAM-001",
                "item_group": "원자재",
                "min_amount": 0,
                "max_amount": 1000000,
                "approver": "team-lead",
                "is_active": True,
            },
            {
                "_id": "BAM-002",
                "item_group": "원자재",
                "min_amount": 1000001,
                "max_amount": 10000000,
                "approver": "director",
                "is_active": True,
            },
        ]

        result = service.get_approver("원자재", 500000)

        assert result["approver"] == "team-lead"
        assert result["matrix_id"] == "BAM-001"

    def test_고금액_결재자(self) -> None:
        service, matrix_repo = _make_service()
        matrix_repo.find_many.return_value = [
            {
                "_id": "BAM-001",
                "min_amount": 0,
                "max_amount": 1000000,
                "approver": "team-lead",
                "is_active": True,
            },
            {
                "_id": "BAM-002",
                "min_amount": 1000001,
                "max_amount": 10000000,
                "approver": "director",
                "is_active": True,
            },
        ]

        result = service.get_approver("원자재", 5000000)

        assert result["approver"] == "director"

    def test_매칭_없으면_에러(self) -> None:
        service, matrix_repo = _make_service()
        matrix_repo.find_many.return_value = []

        with pytest.raises(OneERPError) as exc_info:
            service.get_approver("원자재", 100)
        assert "승인 매트릭스가 없습니다" in (exc_info.value.detail or "")


class Test전체결재자조회:
    """get_all_approvers_for_amount 테스트."""

    def test_금액_기반_전체_결재자(self) -> None:
        service, matrix_repo = _make_service()
        matrix_repo.find_many.return_value = [
            {
                "_id": "BAM-001",
                "item_group": "원자재",
                "min_amount": 0,
                "max_amount": 1000000,
                "approver": "lead-A",
                "is_active": True,
            },
            {
                "_id": "BAM-002",
                "item_group": "소모품",
                "min_amount": 0,
                "max_amount": 500000,
                "approver": "lead-B",
                "is_active": True,
            },
            {
                "_id": "BAM-003",
                "item_group": "설비",
                "min_amount": 1000000,
                "max_amount": 50000000,
                "approver": "cfo",
                "is_active": True,
            },
        ]

        result = service.get_all_approvers_for_amount(300000)

        assert len(result) == 2  # 원자재 + 소모품
        approvers = {r["approver"] for r in result}
        assert approvers == {"lead-A", "lead-B"}
