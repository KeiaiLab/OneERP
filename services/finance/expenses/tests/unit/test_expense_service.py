"""경비 서비스(ExpenseService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_expenses_app.services.expense_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_expenses_app.services.expense_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_expenses_app.services.expense_service import ExpenseService

        service = ExpenseService(tenant_id="test-tenant")
    return (
        service,
        repos["corporate_card_transactions"],
        repos["expense_claims"],
        repos["travel_requests"],
    )


class Test법인카드매칭:
    def test_금액일치_자동매칭(self) -> None:
        service, cct_repo, claim_repo, _travel = _make_service()
        cct_repo.find_many.return_value = [
            {"_id": "CCT-001", "amount": 50000, "merchant": "식당A"},
            {"_id": "CCT-002", "amount": 30000, "merchant": "택시"},
        ]
        claim_repo.find_many.return_value = [
            {"_id": "EC-001", "total_amount": 50000, "approval_status": "pending"},
        ]

        result = service.match_card_transactions("EMP-001", "1234-5678")

        assert result["matched_count"] == 1
        assert len(result["unmatched_transactions"]) == 1
        assert len(result["unmatched_claims"]) == 0

    def test_거래없으면_빈결과(self) -> None:
        service, cct_repo, claim_repo, _travel = _make_service()
        cct_repo.find_many.return_value = []
        claim_repo.find_many.return_value = []

        result = service.match_card_transactions("EMP-001", "1234-5678")

        assert result["matched_count"] == 0


class Test거래기반_경비청구:
    def test_자동_경비청구_생성(self) -> None:
        service, cct_repo, claim_repo, _travel = _make_service()
        cct_repo.find_by_id.return_value = {
            "_id": "CCT-001",
            "amount": 50000,
            "merchant": "식당A",
            "transaction_date": "2026-03-15",
        }

        result = service.create_claim_from_transaction("CCT-001", "EMP-001")

        assert result["claim_id"] == "EC-001"
        assert result["amount"] == 50000.0
        claim_repo.insert.assert_called_once()

    def test_거래_미존재_에러(self) -> None:
        service, cct_repo, _claim, _travel = _make_service()
        cct_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.create_claim_from_transaction("CCT-999", "EMP-001")


class Test출장정산:
    def test_정상_정산(self) -> None:
        service, _cct, claim_repo, travel_repo = _make_service()
        travel_repo.find_by_id.return_value = {
            "_id": "TR-001",
            "employee": "EMP-001",
            "estimated_cost": 500000,
        }

        result = service.settle_travel(
            "TR-001",
            [
                {"expense_type": "숙박", "amount": 200000, "description": "호텔"},
                {"expense_type": "교통", "amount": 150000, "description": "KTX"},
            ],
        )

        assert result["estimated_cost"] == 500000
        assert result["actual_cost"] == 350000
        assert result["difference"] == -150000.0
        claim_repo.insert.assert_called_once()
        travel_repo.update_by_id.assert_called_once()

    def test_출장_미존재_에러(self) -> None:
        service, _cct, _claim, travel_repo = _make_service()
        travel_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.settle_travel("TR-999", [])
