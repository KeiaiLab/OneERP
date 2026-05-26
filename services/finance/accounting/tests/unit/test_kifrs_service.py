"""K-IFRS 매핑 및 재무제표 변환 서비스 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def kifrs_service(mock_collection):
    """KIFRSService 인스턴스를 생성한다.

    mock_collection은 conftest에서 제공하며,
    여기서는 서비스 내부의 3개 Repository가 모두 같은 mock_collection을 사용한다.
    """
    from oneerp_accounting_app.services.kifrs_service import KIFRSService

    return KIFRSService(tenant_id="test-tenant")


class TestMapAccount:
    """map_account 메서드 테스트."""

    def test_매핑_존재시_kifrs_계정_반환(self, kifrs_service, mock_collection):
        """로컬 계정에 대한 K-IFRS 매핑이 존재하면 변환된 계정을 반환한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {
                "local_account": "현금",
                "k_ifrs_account": "K-현금및현금성자산",
                "is_active": True,
            }
        ]

        result = kifrs_service.map_account("현금")

        assert result == "K-현금및현금성자산"

    def test_매핑_없으면_none_반환(self, kifrs_service, mock_collection):
        """매핑이 없는 계정은 None을 반환한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = []

        result = kifrs_service.map_account("미등록계정")

        assert result is None


class TestValidateMappingCompleteness:
    """validate_mapping_completeness 메서드 테스트."""

    def test_전체_매핑_완료(self, kifrs_service, mock_collection):
        """모든 계정이 매핑되어 있으면 coverage 100%를 반환한다."""
        # 첫 번째 find_many 호출: 계정 목록 조회
        # 이후 map_account가 각 계정에 대해 find_many를 호출
        accounts = [
            {"account_name": "현금", "is_group": False},
            {"account_name": "매출", "is_group": False},
        ]
        mapping_현금 = [{"local_account": "현금", "k_ifrs_account": "K-현금", "is_active": True}]
        mapping_매출 = [{"local_account": "매출", "k_ifrs_account": "K-매출", "is_active": True}]

        call_count = 0

        def mock_find_side_effect(*_args, **_kwargs):
            """find 호출 순서에 따라 다른 결과를 반환한다."""
            nonlocal call_count
            mock_cursor = MagicMock()
            mock_skip = MagicMock()
            mock_cursor.skip.return_value = mock_skip

            results_sequence = [accounts, mapping_현금, mapping_매출]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        result = kifrs_service.validate_mapping_completeness()

        assert result["total_accounts"] == 2
        assert result["mapped"] == 2
        assert result["unmapped"] == []
        assert result["coverage_pct"] == 100.0

    def test_부분_매핑_누락_목록(self, kifrs_service, mock_collection):
        """일부 계정에 매핑이 없으면 unmapped 목록에 포함된다."""
        accounts = [
            {"account_name": "현금", "is_group": False},
            {"account_name": "미지급금", "is_group": False},
            {"account_name": "급여", "is_group": False},
        ]
        mapping_현금 = [{"local_account": "현금", "k_ifrs_account": "K-현금", "is_active": True}]

        call_count = 0

        def mock_find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            mock_cursor = MagicMock()
            mock_skip = MagicMock()
            mock_cursor.skip.return_value = mock_skip

            # 순서: 계정목록, 현금매핑(있음), 미지급금매핑(없음), 급여매핑(없음)
            results_sequence = [accounts, mapping_현금, [], []]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        result = kifrs_service.validate_mapping_completeness()

        assert result["total_accounts"] == 3
        assert result["mapped"] == 1
        assert result["unmapped"] == ["미지급금", "급여"]
        assert result["coverage_pct"] == 33.33

    def test_계정_없으면_빈_결과(self, kifrs_service, mock_collection):
        """계정이 없으면 빈 결과를 반환한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = []

        result = kifrs_service.validate_mapping_completeness()

        assert result["total_accounts"] == 0
        assert result["mapped"] == 0
        assert result["unmapped"] == []
        assert result["coverage_pct"] == 100.0


class TestGenerateFinancialStatement:
    """generate_financial_statement 메서드 테스트."""

    def _make_journal(self, items: list[dict]) -> dict:
        """테스트용 분개전표 딕셔너리를 생성한다."""
        return {"items": items, "docstatus": 1}

    def test_재무상태표_균형(self, kifrs_service, mock_collection):
        """재무상태표에서 자산 = 부채 + 자본이 성립해야 한다."""
        # 분개: 현금(자산) 1000 차변 / 차입금(부채) 700 대변 + 자본금(자본) 300 대변
        journals = [
            self._make_journal(
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

            # 순서:
            # 1. 전표 조회
            # 2. _aggregate_by_account → map_account("현금"), map_account("차입금"), map_account("자본금")
            # 3. _get_account_type_map: 계정 목록 조회 + 각 계정 map_account
            # map_account는 매핑 없음 → 원본 계정 사용
            results_sequence = [
                journals,  # 전표 조회
                [],  # map_account("현금") → 없음
                [],  # map_account("차입금") → 없음
                [],  # map_account("자본금") → 없음
                accounts,  # _get_account_type_map 계정 조회
                [],  # map_account("현금") → 없음
                [],  # map_account("차입금") → 없음
                [],  # map_account("자본금") → 없음
            ]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        result = kifrs_service.generate_financial_statement(
            date(2026, 1, 1),
            date(2026, 3, 31),
            "balance_sheet",
        )

        assert result["statement_type"] == "balance_sheet"
        assert result["is_balanced"] is True
        assert result["sections"]["assets"]["total"] == 1000.0
        assert result["sections"]["liabilities"]["total"] == 700.0
        assert result["sections"]["equity"]["total"] == 300.0

    def test_손익계산서_순이익(self, kifrs_service, mock_collection):
        """손익계산서에서 당기순이익이 정확히 계산되어야 한다."""
        # 매출(수익) 5000 대변, 급여(비용) 3000 차변 → 순이익 2000
        journals = [
            self._make_journal(
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
                journals,  # 전표 조회
                [],  # map_account("매출") → 없음
                [],  # map_account("급여") → 없음
                accounts,  # _get_account_type_map
                [],  # map_account("매출") → 없음
                [],  # map_account("급여") → 없음
            ]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        result = kifrs_service.generate_financial_statement(
            date(2026, 1, 1),
            date(2026, 3, 31),
            "income_statement",
        )

        assert result["statement_type"] == "income_statement"
        assert result["sections"]["income"]["total"] == 5000.0
        assert result["sections"]["expenses"]["total"] == 3000.0
        assert result["net_income"] == 2000.0

    def test_전표_없는_기간_빈_재무제표(self, kifrs_service, mock_collection):
        """전표가 없는 기간에는 모든 항목이 0인 빈 재무제표를 반환한다."""
        call_count = 0

        def mock_find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            mock_cursor = MagicMock()
            mock_skip = MagicMock()
            mock_cursor.skip.return_value = mock_skip

            # 전표 조회: 없음, 계정 조회: 없음
            mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        result = kifrs_service.generate_financial_statement(
            date(2026, 7, 1),
            date(2026, 9, 30),
            "balance_sheet",
        )

        assert result["statement_type"] == "balance_sheet"
        assert result["sections"]["assets"]["total"] == 0
        assert result["sections"]["liabilities"]["total"] == 0
        assert result["sections"]["equity"]["total"] == 0
        assert result["is_balanced"] is True

    def test_kifrs_매핑_적용(self, kifrs_service, mock_collection):
        """K-IFRS 매핑이 있는 계정은 변환된 계정명으로 집계된다."""
        journals = [
            self._make_journal(
                [
                    {"account": "현금", "debit": 500.0, "credit": 0.0},
                    {"account": "미지급금", "debit": 0.0, "credit": 500.0},
                ]
            ),
        ]
        mapping_현금 = [
            {"local_account": "현금", "k_ifrs_account": "K-현금및현금성자산", "is_active": True},
        ]
        accounts = [
            {"account_name": "현금", "account_type": "asset"},
            {"account_name": "미지급금", "account_type": "liability"},
        ]

        call_count = 0

        def mock_find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            mock_cursor = MagicMock()
            mock_skip = MagicMock()
            mock_cursor.skip.return_value = mock_skip

            results_sequence = [
                journals,  # 전표 조회
                mapping_현금,  # map_account("현금") → K-현금및현금성자산
                [],  # map_account("미지급금") → 없음, 원본 사용
                accounts,  # _get_account_type_map
                mapping_현금,  # map_account("현금") → K-현금및현금성자산
                [],  # map_account("미지급금") → 없음
            ]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        result = kifrs_service.generate_financial_statement(
            date(2026, 1, 1),
            date(2026, 3, 31),
            "balance_sheet",
        )

        # K-IFRS 변환된 계정명 확인
        asset_accounts = [item["account"] for item in result["sections"]["assets"]["items"]]
        assert "K-현금및현금성자산" in asset_accounts
        assert result["is_balanced"] is True

    def test_매핑_없는_계정_원본_사용(self, kifrs_service, mock_collection):
        """K-IFRS 매핑이 없는 계정은 원본 계정명을 그대로 사용한다."""
        journals = [
            self._make_journal(
                [
                    {"account": "토지", "debit": 2000.0, "credit": 0.0},
                    {"account": "자본금", "debit": 0.0, "credit": 2000.0},
                ]
            ),
        ]
        accounts = [
            {"account_name": "토지", "account_type": "asset"},
            {"account_name": "자본금", "account_type": "equity"},
        ]

        call_count = 0

        def mock_find_side_effect(*_args, **_kwargs):
            nonlocal call_count
            mock_cursor = MagicMock()
            mock_skip = MagicMock()
            mock_cursor.skip.return_value = mock_skip

            results_sequence = [
                journals,  # 전표 조회
                [],  # map_account("토지") → 없음
                [],  # map_account("자본금") → 없음
                accounts,  # _get_account_type_map
                [],  # map_account("토지") → 없음
                [],  # map_account("자본금") → 없음
            ]
            if call_count < len(results_sequence):
                mock_skip.limit.return_value = results_sequence[call_count]
            else:
                mock_skip.limit.return_value = []
            call_count += 1
            return mock_cursor

        mock_collection.find.side_effect = mock_find_side_effect

        result = kifrs_service.generate_financial_statement(
            date(2026, 1, 1),
            date(2026, 3, 31),
            "balance_sheet",
        )

        # 원본 계정명 사용 확인
        asset_accounts = [item["account"] for item in result["sections"]["assets"]["items"]]
        assert "토지" in asset_accounts
        equity_accounts = [item["account"] for item in result["sections"]["equity"]["items"]]
        assert "자본금" in equity_accounts
        assert result["is_balanced"] is True
