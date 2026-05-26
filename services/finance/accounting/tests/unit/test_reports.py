"""재무제표 보고서 API 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app
from oneerp_core.document import DocStatus

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


_BASE_URL = "/api/v1/reports"


def _make_journal(items: list[dict]) -> dict:
    """테스트용 분개전표 딕셔너리를 생성한다."""
    return {"items": items, "docstatus": DocStatus.SUBMITTED}


class TestBalanceSheet:
    """GET /api/v1/reports/balance-sheet 테스트."""

    def test_재무상태표_정상_조회(self, mock_collection: MagicMock) -> None:
        """기간 내 전표를 집계하여 재무상태표를 반환한다."""
        journals = [
            _make_journal(
                [
                    {"account": "현금", "debit": 1000.0, "credit": 0.0},
                    {"account": "차입금", "debit": 0.0, "credit": 700.0},
                    {"account": "자본금", "debit": 0.0, "credit": 300.0},
                ]
            ),
        ]
        accounts = [
            {"account_name": "현금", "account_type": "asset"},
            {"account_name": "차입금", "account_type": "liability"},
            {"account_name": "자본금", "account_type": "equity"},
        ]

        call_count = 0

        def mock_find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            mock_cursor = MagicMock()
            mock_skip = MagicMock()
            mock_cursor.skip.return_value = mock_skip

            # 순서: 전표 조회 → map_account x3 → 계정 목록 → map_account x3
            results_sequence = [
                journals,
                [],  # map_account("현금")
                [],  # map_account("차입금")
                [],  # map_account("자본금")
                accounts,  # _get_account_type_map
                [],  # map_account("현금")
                [],  # map_account("차입금")
                [],  # map_account("자본금")
            ]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        response = client.get(
            f"{_BASE_URL}/balance-sheet",
            params={"period_start": "2026-01-01", "period_end": "2026-03-31"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["statement_type"] == "balance_sheet"
        assert data["is_balanced"] is True
        assert data["sections"]["assets"]["total"] == 1000.0
        assert data["sections"]["liabilities"]["total"] == 700.0
        assert data["sections"]["equity"]["total"] == 300.0

    def test_기간_파라미터_누락_422(self, mock_collection: MagicMock) -> None:
        """필수 query param이 없으면 422를 반환한다."""
        response = client.get(f"{_BASE_URL}/balance-sheet")
        assert response.status_code == 422


class TestIncomeStatement:
    """GET /api/v1/reports/income-statement 테스트."""

    def test_손익계산서_정상_조회(self, mock_collection: MagicMock) -> None:
        """기간 내 전표를 집계하여 손익계산서를 반환한다."""
        journals = [
            _make_journal(
                [
                    {"account": "매출", "debit": 0.0, "credit": 5000.0},
                    {"account": "급여", "debit": 3000.0, "credit": 0.0},
                ]
            ),
        ]
        accounts = [
            {"account_name": "매출", "account_type": "income"},
            {"account_name": "급여", "account_type": "expense"},
        ]

        call_count = 0

        def mock_find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            mock_cursor = MagicMock()
            mock_skip = MagicMock()
            mock_cursor.skip.return_value = mock_skip

            results_sequence = [
                journals,
                [],  # map_account("매출")
                [],  # map_account("급여")
                accounts,  # _get_account_type_map
                [],  # map_account("매출")
                [],  # map_account("급여")
            ]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        response = client.get(
            f"{_BASE_URL}/income-statement",
            params={"period_start": "2026-01-01", "period_end": "2026-03-31"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["statement_type"] == "income_statement"
        assert data["sections"]["income"]["total"] == 5000.0
        assert data["sections"]["expenses"]["total"] == 3000.0
        assert data["net_income"] == 2000.0


class TestTrialBalance:
    """GET /api/v1/reports/trial-balance 테스트."""

    def test_시산표_정상_조회(self, mock_collection: MagicMock) -> None:
        """제출된 전표의 계정별 차변/대변 합계를 반환한다."""
        journals = [
            _make_journal(
                [
                    {"account": "현금", "debit": 1000.0, "credit": 0.0},
                    {"account": "매출", "debit": 0.0, "credit": 1000.0},
                ]
            ),
            _make_journal(
                [
                    {"account": "급여", "debit": 500.0, "credit": 0.0},
                    {"account": "현금", "debit": 0.0, "credit": 500.0},
                ]
            ),
        ]

        mock_collection.find.return_value.skip.return_value.limit.return_value = journals

        response = client.get(
            f"{_BASE_URL}/trial-balance",
            params={"period_start": "2026-01-01", "period_end": "2026-03-31"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "trial_balance"
        assert data["is_balanced"] is True
        assert data["total_debit"] == 1500.0
        assert data["total_credit"] == 1500.0

        # 계정별 검증
        items_by_account = {item["account"]: item for item in data["items"]}
        assert items_by_account["현금"]["debit"] == 1000.0
        assert items_by_account["현금"]["credit"] == 500.0
        assert items_by_account["현금"]["balance"] == 500.0
        assert items_by_account["매출"]["credit"] == 1000.0
        assert items_by_account["급여"]["debit"] == 500.0

    def test_전표_없는_기간_빈_시산표(self, mock_collection: MagicMock) -> None:
        """전표가 없는 기간에는 빈 시산표를 반환한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = []

        response = client.get(
            f"{_BASE_URL}/trial-balance",
            params={"period_start": "2026-07-01", "period_end": "2026-09-30"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_debit"] == 0.0
        assert data["total_credit"] == 0.0
        assert data["is_balanced"] is True

    def test_기간_파라미터_누락_422(self, mock_collection: MagicMock) -> None:
        """필수 query param이 없으면 422를 반환한다."""
        response = client.get(f"{_BASE_URL}/trial-balance")
        assert response.status_code == 422
