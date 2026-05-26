"""부가세 자동 세액 계산 서비스 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# 테스트 헬퍼
# ---------------------------------------------------------------------------


def _make_journal(posting_date: str, items: list[dict], docstatus: int = 1) -> dict:
    """테스트용 분개전표 딕셔너리를 생성한다."""
    return {
        "_id": f"JE-{posting_date}",
        "posting_date": posting_date,
        "docstatus": docstatus,
        "items": items,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vat_service(mock_collection):
    """VATService 인스턴스를 생성한다."""
    from oneerp_accounting_app.services.vat_service import VATService

    return VATService("test-tenant")


# ---------------------------------------------------------------------------
# calculate_vat 테스트
# ---------------------------------------------------------------------------


class TestCalculateVat:
    """calculate_vat 메서드 테스트."""

    def test_매출세액만_있는_경우(self, vat_service, mock_collection):
        """매출세액 계정만 있을 때 output_tax만 집계된다."""
        journals = [
            _make_journal(
                "2026-01-15",
                [
                    {"account": "매출세액", "debit": 0.0, "credit": 100_000.0},
                ],
            ),
            _make_journal(
                "2026-02-10",
                [
                    {"account": "매출세액", "debit": 0.0, "credit": 50_000.0},
                ],
            ),
        ]
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: journals),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["output_tax"] == 150_000.0
        assert result["input_tax"] == 0.0
        assert result["net_tax"] == 150_000.0
        assert result["journal_count"] == 2

    def test_매입세액만_있는_경우(self, vat_service, mock_collection):
        """매입세액 계정만 있을 때 input_tax만 집계된다."""
        journals = [
            _make_journal(
                "2026-01-20",
                [
                    {"account": "매입세액", "debit": 80_000.0, "credit": 0.0},
                ],
            ),
        ]
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: journals),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["output_tax"] == 0.0
        assert result["input_tax"] == 80_000.0
        assert result["net_tax"] == -80_000.0

    def test_매출_매입_모두_있는_경우(self, vat_service, mock_collection):
        """매출세액과 매입세액이 모두 있을 때 net_tax = output - input."""
        journals = [
            _make_journal(
                "2026-02-01",
                [
                    {"account": "매출세액", "debit": 0.0, "credit": 200_000.0},
                    {"account": "매입세액", "debit": 120_000.0, "credit": 0.0},
                ],
            ),
        ]
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: journals),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["output_tax"] == 200_000.0
        assert result["input_tax"] == 120_000.0
        assert result["net_tax"] == 80_000.0
        assert result["journal_count"] == 1

    def test_전표가_없는_경우(self, vat_service, mock_collection):
        """전표가 없으면 모든 세액이 0이다."""
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: []),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["output_tax"] == 0.0
        assert result["input_tax"] == 0.0
        assert result["net_tax"] == 0.0
        assert result["journal_count"] == 0

    def test_output_tax_영문_계정_인식(self, vat_service, mock_collection):
        """영문 'output_tax' 계정명도 매출세액으로 인식된다."""
        journals = [
            _make_journal(
                "2026-01-15",
                [
                    {"account": "output_tax", "debit": 0.0, "credit": 300_000.0},
                ],
            ),
        ]
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: journals),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["output_tax"] == 300_000.0

    def test_input_tax_영문_계정_인식(self, vat_service, mock_collection):
        """영문 'input_tax' 계정명도 매입세액으로 인식된다."""
        journals = [
            _make_journal(
                "2026-02-20",
                [
                    {"account": "input_tax", "debit": 45_000.0, "credit": 0.0},
                ],
            ),
        ]
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: journals),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["input_tax"] == 45_000.0

    def test_비세액_계정은_집계에서_제외(self, vat_service, mock_collection):
        """세액 키워드가 없는 계정은 집계에 포함되지 않는다."""
        journals = [
            _make_journal(
                "2026-01-15",
                [
                    {"account": "매출", "debit": 0.0, "credit": 1_000_000.0},
                    {"account": "현금", "debit": 1_000_000.0, "credit": 0.0},
                    {"account": "매출세액", "debit": 0.0, "credit": 100_000.0},
                ],
            ),
        ]
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: journals),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["output_tax"] == 100_000.0
        assert result["input_tax"] == 0.0

    def test_복수_전표_다건_합산(self, vat_service, mock_collection):
        """여러 전표의 세액이 올바르게 합산된다."""
        journals = [
            _make_journal(
                "2026-01-10",
                [
                    {"account": "매출세액", "debit": 0.0, "credit": 100_000.0},
                    {"account": "매입세액", "debit": 30_000.0, "credit": 0.0},
                ],
            ),
            _make_journal(
                "2026-02-15",
                [
                    {"account": "output_tax", "debit": 0.0, "credit": 200_000.0},
                    {"account": "input_tax", "debit": 70_000.0, "credit": 0.0},
                ],
            ),
        ]
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: journals),
        )

        result = vat_service.calculate_vat(date(2026, 1, 1), date(2026, 3, 31))

        assert result["output_tax"] == 300_000.0
        assert result["input_tax"] == 100_000.0
        assert result["net_tax"] == 200_000.0
        assert result["journal_count"] == 2


# ---------------------------------------------------------------------------
# create_vat_return 테스트
# ---------------------------------------------------------------------------


class TestCreateVatReturn:
    """create_vat_return 메서드 테스트."""

    def test_중복_신고서_생성_거부(self, vat_service, mock_collection):
        """BR-ACCT-015: 동일 기간 부가세 신고서가 이미 존재하면 ERR-KTAX-020 에러."""
        from oneerp_core.errors import OneERPError

        # 중복 검증: 기존 VATReturn 존재
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(
                limit=lambda _: [
                    {"_id": "VAT-EXIST", "period": "2026-01-01~2026-03-31"},
                ]
            ),
        )

        with pytest.raises(OneERPError, match="ERR-KTAX-020"):
            vat_service.create_vat_return(date(2026, 1, 1), date(2026, 3, 31))

    def test_부가세_신고서_생성(self, vat_service, mock_collection):
        """VATReturn 문서가 올바른 데이터로 생성된다."""
        journals = [
            _make_journal(
                "2026-01-15",
                [
                    {"account": "매출세액", "debit": 0.0, "credit": 500_000.0},
                    {"account": "매입세액", "debit": 200_000.0, "credit": 0.0},
                ],
            ),
        ]
        # 첫 번째 find: 중복 검증 (빈 결과), 두 번째 find: 분개전표 조회
        call_count = {"n": 0}

        def _find_side_effect(*_args, **_kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # 중복 검증: 기존 VATReturn 없음
                return MagicMock(skip=lambda _: MagicMock(limit=lambda _: []))
            # 분개전표 조회
            return MagicMock(skip=lambda _: MagicMock(limit=lambda _: journals))

        mock_collection.find.side_effect = _find_side_effect
        mock_collection.insert_one.return_value = MagicMock(inserted_id="VAT-001")

        doc_id = vat_service.create_vat_return(date(2026, 1, 1), date(2026, 3, 31))

        assert doc_id == "VAT-001"
        mock_collection.insert_one.assert_called_once()
        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert inserted_doc["period"] == "2026-01-01~2026-03-31"
        assert inserted_doc["status"] == "draft"


# ---------------------------------------------------------------------------
# get_tax_summary 테스트
# ---------------------------------------------------------------------------


class TestGetTaxSummary:
    """get_tax_summary 메서드 테스트."""

    def test_기존_신고서_요약_조회(self, vat_service, mock_collection):
        """저장된 VATReturn의 요약 정보를 반환한다."""
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(
                limit=lambda _: [
                    {
                        "_id": "VAT-001",
                        "period": "2026-01-01~2026-03-31",
                        "output_tax": 500_000.0,
                        "input_tax": 200_000.0,
                        "net_tax": 300_000.0,
                        "status": "draft",
                    },
                ]
            ),
        )

        summary = vat_service.get_tax_summary("2026-01-01~2026-03-31")

        assert summary["output_tax"] == 500_000.0
        assert summary["input_tax"] == 200_000.0
        assert summary["net_tax"] == 300_000.0
        assert summary["status"] == "draft"
        assert summary["doc_id"] == "VAT-001"

    def test_신고서_미존재시_not_found(self, vat_service, mock_collection):
        """해당 기간 신고서가 없으면 not_found 상태를 반환한다."""
        mock_collection.find.return_value = MagicMock(
            skip=lambda _: MagicMock(limit=lambda _: []),
        )

        summary = vat_service.get_tax_summary("2026-04-01~2026-06-30")

        assert summary["status"] == "not_found"
        assert summary["doc_id"] is None
        assert summary["output_tax"] == 0.0
