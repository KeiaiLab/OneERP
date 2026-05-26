"""은행 대사 서비스(BankReconciliationService) 단위 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 테스트 전체 기간 동안 모킹한다."""
    with patch(
        "oneerp_accounting_app.services.bank_reconciliation_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """BankReconciliationService와 모킹된 Repository를 반환한다."""
    with patch(
        "oneerp_accounting_app.services.bank_reconciliation_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.bank_reconciliation_service import (
            BankReconciliationService,
        )

        service = BankReconciliationService(tenant_id="test-tenant")

    return service, repos["bank_reconciliations"], repos["journal_entries"]


def _bank_journal_entries(bank_account: str) -> list[dict]:
    """은행 계정 분개전표 테스트 데이터."""
    return [
        {
            "_id": "JE-001",
            "posting_date": "2026-01-15",
            "docstatus": 1,
            "items": [
                {"account": bank_account, "debit": 5000, "credit": 0},
                {"account": "ACC-매출", "debit": 0, "credit": 5000},
            ],
        },
        {
            "_id": "JE-002",
            "posting_date": "2026-01-20",
            "docstatus": 1,
            "items": [
                {"account": bank_account, "debit": 0, "credit": 2000},
                {"account": "ACC-비용", "debit": 2000, "credit": 0},
            ],
        },
    ]


class Test은행대사생성:
    """create_reconciliation 테스트."""

    def test_대사생성_잔액일치(self) -> None:
        """은행 잔액과 시스템 잔액이 일치하면 차이=0."""
        service, br_repo, je_repo = _make_service()
        je_repo.find_many.return_value = _bank_journal_entries("ACC-은행")

        result = service.create_reconciliation(
            bank_account="ACC-은행",
            from_date="2026-01-01",
            to_date="2026-01-31",
            bank_balance=3000.0,  # 5000 - 2000 = 3000
        )

        assert result["system_balance"] == 3000.0
        assert result["difference"] == 0.0
        assert result["is_reconciled"] is True
        br_repo.insert.assert_called_once()

    def test_대사생성_잔액불일치(self) -> None:
        """은행 잔액과 시스템 잔액이 다르면 차이 발생."""
        service, _br_repo, je_repo = _make_service()
        je_repo.find_many.return_value = _bank_journal_entries("ACC-은행")

        result = service.create_reconciliation(
            bank_account="ACC-은행",
            from_date="2026-01-01",
            to_date="2026-01-31",
            bank_balance=3500.0,  # 실제 3000, 차이 500
        )

        assert result["system_balance"] == 3000.0
        assert result["difference"] == 500.0
        assert result["is_reconciled"] is False

    def test_전표없으면_시스템잔액_0(self) -> None:
        service, _br_repo, je_repo = _make_service()
        je_repo.find_many.return_value = []

        result = service.create_reconciliation(
            bank_account="ACC-은행",
            from_date="2026-01-01",
            to_date="2026-01-31",
            bank_balance=1000.0,
        )

        assert result["system_balance"] == 0.0
        assert result["difference"] == 1000.0


class Test자동매칭:
    """auto_match 테스트."""

    def test_금액일치_자동매칭(self) -> None:
        """동일 금액의 은행 거래와 시스템 전표가 자동 매칭된다."""
        service, br_repo, je_repo = _make_service()
        br_repo.find_by_id.return_value = {
            "_id": "BR-001",
            "bank_account": "ACC-은행",
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
        }
        je_repo.find_many.return_value = _bank_journal_entries("ACC-은행")

        bank_txns = [
            {"reference": "TXN-001", "amount": 5000.0, "date": "2026-01-15"},
            {"reference": "TXN-002", "amount": -2000.0, "date": "2026-01-20"},
        ]

        result = service.auto_match(br_id="BR-001", bank_transactions=bank_txns)

        # 시스템 전표의 net_amount: JE-001=5000, JE-002=-2000
        # 은행 거래: TXN-001=5000, TXN-002=-2000 → 둘 다 매칭
        assert result["matched_count"] == 2
        assert len(result["unmatched_bank"]) == 0
        assert len(result["unmatched_system"]) == 0

    def test_미존재_대사_에러(self) -> None:
        service, br_repo, _je = _make_service()
        br_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.auto_match("BR-999", bank_transactions=[])

    def test_빈거래_빈매칭(self) -> None:
        service, br_repo, je_repo = _make_service()
        br_repo.find_by_id.return_value = {
            "_id": "BR-001",
            "bank_account": "ACC-은행",
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
        }
        je_repo.find_many.return_value = []

        result = service.auto_match(br_id="BR-001", bank_transactions=[])

        assert result["matched_count"] == 0
        assert result["unmatched_bank"] == []
        assert result["unmatched_system"] == []


class Test허용오차:
    """BR-ACCT-014: 은행 대사 자동 매칭 허용 오차 테스트."""

    def test_허용오차_이내_매칭_성공(self) -> None:
        """BR-ACCT-014: 금액 차이가 0.01 이하면 자동 매칭된다."""
        service, br_repo, je_repo = _make_service()
        br_repo.find_by_id.return_value = {
            "_id": "BR-TOL",
            "bank_account": "ACC-은행",
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
        }
        # 시스템 전표: 5000.005 (net_amount)
        je_repo.find_many.return_value = [
            {
                "_id": "JE-TOL",
                "posting_date": "2026-01-15",
                "docstatus": 1,
                "items": [
                    {"account": "ACC-은행", "debit": 5000.005, "credit": 0},
                ],
            },
        ]

        # 은행 거래: 5000.00 — 차이 0.005 < 0.01 허용 오차
        result = service.auto_match(
            br_id="BR-TOL",
            bank_transactions=[{"reference": "TXN-TOL", "amount": 5000.00}],
        )

        assert result["matched_count"] == 1

    def test_허용오차_초과_매칭_실패(self) -> None:
        """BR-ACCT-014: 금액 차이가 0.01 초과면 매칭되지 않는다."""
        service, br_repo, je_repo = _make_service()
        br_repo.find_by_id.return_value = {
            "_id": "BR-TOL2",
            "bank_account": "ACC-은행",
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
        }
        je_repo.find_many.return_value = [
            {
                "_id": "JE-TOL2",
                "posting_date": "2026-01-15",
                "docstatus": 1,
                "items": [
                    {"account": "ACC-은행", "debit": 5000.02, "credit": 0},
                ],
            },
        ]

        # 은행 거래: 5000.00 — 차이 0.02 > 0.01 허용 오차
        result = service.auto_match(
            br_id="BR-TOL2",
            bank_transactions=[{"reference": "TXN-TOL2", "amount": 5000.00}],
        )

        assert result["matched_count"] == 0
        assert len(result["unmatched_bank"]) == 1

    def test_대사_생성시_허용오차_이내_reconciled(self) -> None:
        """BR-ACCT-014: 은행-시스템 잔액 차이가 허용오차 이내면 is_reconciled=True."""
        service, _br_repo, je_repo = _make_service()
        je_repo.find_many.return_value = [
            {
                "_id": "JE-REC",
                "posting_date": "2026-01-15",
                "docstatus": 1,
                "items": [
                    {"account": "ACC-은행", "debit": 3000.00, "credit": 0},
                ],
            },
        ]

        # 시스템잔액=3000.00, 은행잔액=3000.005 → 차이 round(2)=0.00 → 허용오차 이내
        result = service.create_reconciliation(
            bank_account="ACC-은행",
            from_date="2026-01-01",
            to_date="2026-01-31",
            bank_balance=3000.005,
        )

        assert result["is_reconciled"] is True


class Test미대사항목조회:
    """get_unreconciled_entries 테스트."""

    def test_미대사_항목_조회(self) -> None:
        service, _br, je_repo = _make_service()
        je_repo.find_many.return_value = _bank_journal_entries("ACC-은행")

        items = service.get_unreconciled_entries(
            bank_account="ACC-은행",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )

        assert len(items) == 2
        assert items[0]["journal_entry_id"] == "JE-001"
        assert items[0]["net_amount"] == Decimal(5000)
        assert items[1]["net_amount"] == Decimal(-2000)


class TestDecimal일관성:
    """float→Decimal 변환 일관성 검증."""

    def test_system_balance_decimal_정밀도(self) -> None:
        """_calculate_system_balance가 Decimal 기반으로 정밀 계산한다."""
        service, _br_repo, je_repo = _make_service()
        # float 부동소수점 오류 유발 데이터: 0.1 + 0.2 != 0.3
        je_repo.find_many.return_value = [
            {
                "_id": "JE-DEC1",
                "posting_date": "2026-01-10",
                "docstatus": 1,
                "items": [
                    {"account": "ACC-은행", "debit": 0.1, "credit": 0},
                ],
            },
            {
                "_id": "JE-DEC2",
                "posting_date": "2026-01-11",
                "docstatus": 1,
                "items": [
                    {"account": "ACC-은행", "debit": 0.2, "credit": 0},
                ],
            },
        ]

        result = service.create_reconciliation(
            bank_account="ACC-은행",
            from_date="2026-01-01",
            to_date="2026-01-31",
            bank_balance=0.3,
        )

        # Decimal 기반이므로 0.1 + 0.2 = 0.3 정확히 일치
        assert result["system_balance"] == 0.3
        assert result["difference"] == 0.0
        assert result["is_reconciled"] is True

    def test_extract_bank_items_decimal_타입(self) -> None:
        """_extract_bank_items가 Decimal 타입을 반환한다."""
        service, _br_repo, je_repo = _make_service()
        je_repo.find_many.return_value = _bank_journal_entries("ACC-은행")

        items = service.get_unreconciled_entries(
            bank_account="ACC-은행",
            from_date="2026-01-01",
            to_date="2026-01-31",
        )

        assert isinstance(items[0]["debit"], Decimal)
        assert isinstance(items[0]["credit"], Decimal)
        assert isinstance(items[0]["net_amount"], Decimal)
