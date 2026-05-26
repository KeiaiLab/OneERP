"""소거 서비스(EliminationService) 단위 테스트.

BR-CSL-002: 소거 전표 차대변 일치
BR-CSL-006: 내부거래 양방향 대사
BR-CSL-007: 미실현이익 소거 (재고)
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_finance_extra_app.consolidation.models.intercompany_balance import MatchStatus


def _make_service():
    """EliminationService와 모킹된 Repository들을 반환한다."""
    with patch(
        "oneerp_finance_extra_app.consolidation.services.elimination_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_finance_extra_app.consolidation.services.elimination_service import (
            EliminationService,
        )

        service = EliminationService(tenant_id="test-tenant")

    return service, repos


class Test내부거래대사:
    """BR-CSL-006: 내부거래 양방향 대사 테스트."""

    def test_완전일치(self) -> None:
        """동일 금액 → matched."""
        service, _ = _make_service()
        result = service.reconcile_intercompany(
            entity_a_amount=Decimal(100000000),
            entity_b_amount=Decimal(100000000),
        )
        assert result["match_status"] == MatchStatus.MATCHED
        assert result["difference_amount"] == Decimal(0)

    def test_금액_허용오차_내(self) -> None:
        """500원 차이, 허용 1000원 → within_tolerance."""
        service, _ = _make_service()
        result = service.reconcile_intercompany(
            entity_a_amount=Decimal(100000500),
            entity_b_amount=Decimal(100000000),
            tolerance_amount=Decimal(1000),
            tolerance_percentage=Decimal("0.1"),
        )
        assert result["match_status"] == MatchStatus.WITHIN_TOLERANCE
        assert result["difference_amount"] == Decimal(500)

    def test_비율_허용오차_내(self) -> None:
        """0.1% 차이, 허용 0.1% → within_tolerance."""
        service, _ = _make_service()
        result = service.reconcile_intercompany(
            entity_a_amount=Decimal(100100000),
            entity_b_amount=Decimal(100000000),
            tolerance_amount=Decimal(1000),
            tolerance_percentage=Decimal("0.1"),
        )
        assert result["match_status"] == MatchStatus.WITHIN_TOLERANCE

    def test_불일치_초과(self) -> None:
        """1% 차이, 허용 0.1% → mismatch."""
        service, _ = _make_service()
        result = service.reconcile_intercompany(
            entity_a_amount=Decimal(101000000),
            entity_b_amount=Decimal(100000000),
            tolerance_amount=Decimal(1000),
            tolerance_percentage=Decimal("0.1"),
        )
        assert result["match_status"] == MatchStatus.MISMATCH
        assert result["difference_amount"] == Decimal(1000000)

    def test_양쪽_0원(self) -> None:
        """양쪽 0원 → matched."""
        service, _ = _make_service()
        result = service.reconcile_intercompany(
            entity_a_amount=Decimal(0),
            entity_b_amount=Decimal(0),
        )
        assert result["match_status"] == MatchStatus.MATCHED


class Test차대변일치검증:
    """BR-CSL-002: 소거 전표 차대변 일치 검증 테스트."""

    def test_정확히_일치(self) -> None:
        service, _ = _make_service()
        assert service.validate_debit_credit_balance(Decimal(100000000), Decimal(100000000)) is True

    def test_1원이내_오차_통과(self) -> None:
        service, _ = _make_service()
        assert service.validate_debit_credit_balance(Decimal(100000001), Decimal(100000000)) is True

    def test_2원_초과_실패(self) -> None:
        service, _ = _make_service()
        assert (
            service.validate_debit_credit_balance(Decimal(100000002), Decimal(100000000)) is False
        )


class Test미실현이익재고:
    """BR-CSL-007: 재고 미실현이익 산출 테스트."""

    def test_기본케이스(self) -> None:
        """내부매입재고 3천만, 마진율 20% → 미실현이익 6백만."""
        service, _ = _make_service()
        result = service.calculate_unrealized_profit_inventory(
            ending_inventory_amount=Decimal(30000000),
            internal_margin_rate=Decimal("0.20"),
        )
        assert result == Decimal(6000000)

    def test_시나리오_25퍼센트_마진(self) -> None:
        """L3 SC-CSL-003: 6천만 x 25% = 1500만."""
        service, _ = _make_service()
        result = service.calculate_unrealized_profit_inventory(
            ending_inventory_amount=Decimal(60000000),
            internal_margin_rate=Decimal("0.25"),
        )
        assert result == Decimal(15000000)


class Test소거실행:
    """소거 실행 테스트."""

    def test_잔액미수집_시_에러(self) -> None:
        """내부거래 잔액 없으면 ERR-CSL-071."""
        service, repos = _make_service()
        repos["intercompany_balances"].find_many.return_value = []

        with pytest.raises(OneERPError) as exc_info:
            service.execute_elimination("CPER-001")

        assert exc_info.value.error == "ERR-CSL-071"

    def test_불일치_잔존_시_에러(self) -> None:
        """mismatch 잔존 시 ERR-CSL-070."""
        service, repos = _make_service()
        repos["intercompany_balances"].find_many.return_value = [
            {"_id": "ICB-001", "match_status": "mismatch"},
            {"_id": "ICB-002", "match_status": "matched"},
        ]

        with pytest.raises(OneERPError) as exc_info:
            service.execute_elimination("CPER-001")

        assert exc_info.value.error == "ERR-CSL-070"

    def test_정상_소거_실행(self) -> None:
        """매칭 완료 잔액에 대해 소거 실행."""
        service, repos = _make_service()
        repos["intercompany_balances"].find_many.return_value = [
            {
                "_id": "ICB-001",
                "match_status": "matched",
                "entity_a_amount": "200000000",
                "elimination_entry_id": None,
            },
            {
                "_id": "ICB-002",
                "match_status": "within_tolerance",
                "entity_a_amount": "220000000",
                "elimination_entry_id": None,
            },
        ]
        repos["elimination_rules"].find_many.return_value = []

        result = service.execute_elimination("CPER-001")

        assert result["elimination_count"] == 2
        assert result["total_amount"] == Decimal(420000000)

    def test_이미_소거된_잔액_건너뜀(self) -> None:
        """elimination_entry_id가 있는 잔액은 건너뛴다."""
        service, repos = _make_service()
        repos["intercompany_balances"].find_many.return_value = [
            {
                "_id": "ICB-001",
                "match_status": "matched",
                "entity_a_amount": "200000000",
                "elimination_entry_id": "ELIM-001",  # 이미 소거됨
            },
        ]
        repos["elimination_rules"].find_many.return_value = []

        result = service.execute_elimination("CPER-001")

        assert result["elimination_count"] == 0
