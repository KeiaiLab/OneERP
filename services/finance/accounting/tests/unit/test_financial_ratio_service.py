"""재무비율 분석 서비스(FinancialRatioService) 단위 테스트.

테스트 대상 비즈니스 룰:
- BR-ACCT-020 확장: 손익 계산 로직을 활용한 재무비율 산출
- 재무 5대 비율: 유동비율, 부채비율, 자기자본비율, ROA, ROE
- 0 분모 안전 처리 (DivisionByZero 방지)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """FinancialRatioService와 모킹된 Repository를 반환한다."""
    with patch(
        "oneerp_accounting_app.services.financial_ratio_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.financial_ratio_service import FinancialRatioService

        service = FinancialRatioService(tenant_id="test-tenant")

    return service, repos


class Test기본_비율_계산:
    """순수 함수 단위 테스트."""

    def test_유동비율_정상_케이스(self) -> None:
        """유동비율 = 유동자산 / 유동부채. 200/100 = 2.0."""
        from oneerp_accounting_app.services.financial_ratio_service import calculate_current_ratio

        result = calculate_current_ratio(
            current_assets=Decimal(200000000),
            current_liabilities=Decimal(100000000),
        )

        assert result == Decimal("2.00")

    def test_유동비율_분모_0은_None(self) -> None:
        """유동부채가 0이면 None 반환 (계산 불가)."""
        from oneerp_accounting_app.services.financial_ratio_service import calculate_current_ratio

        result = calculate_current_ratio(
            current_assets=Decimal(100000000),
            current_liabilities=Decimal(0),
        )

        assert result is None

    def test_부채비율_총부채_총자본(self) -> None:
        """부채비율 = 총부채 / 총자본. 80/40 x 100 = 200%."""
        from oneerp_accounting_app.services.financial_ratio_service import calculate_debt_ratio

        result = calculate_debt_ratio(
            total_liabilities=Decimal(80000000),
            total_equity=Decimal(40000000),
        )

        assert result == Decimal("200.00")

    def test_자기자본비율_총자본_총자산(self) -> None:
        """자기자본비율 = 총자본 / 총자산 x 100. 40/120 x 100 = 33.33%."""
        from oneerp_accounting_app.services.financial_ratio_service import calculate_equity_ratio

        result = calculate_equity_ratio(
            total_equity=Decimal(40000000),
            total_assets=Decimal(120000000),
        )

        assert result == Decimal("33.33")

    def test_ROA_순이익_총자산(self) -> None:
        """ROA = 당기순이익 / 총자산 x 100. 12/120 x 100 = 10.00%."""
        from oneerp_accounting_app.services.financial_ratio_service import calculate_roa

        result = calculate_roa(
            net_income=Decimal(12000000),
            total_assets=Decimal(120000000),
        )

        assert result == Decimal("10.00")

    def test_ROE_순이익_자기자본(self) -> None:
        """ROE = 당기순이익 / 자기자본 x 100. 12/40 x 100 = 30.00%."""
        from oneerp_accounting_app.services.financial_ratio_service import calculate_roe

        result = calculate_roe(
            net_income=Decimal(12000000),
            total_equity=Decimal(40000000),
        )

        assert result == Decimal("30.00")


class Test재무비율_종합_분석:
    """analyze_ratios 통합 테스트."""

    def test_재무상태표와_손익계산서_기반_5대_비율_계산(self) -> None:
        """제출된 분개전표 집계 후 5대 비율을 산출한다."""
        service, repos = _make_service()

        # 계정과목 마스터: 자산/부채/자본/수익/비용 분류
        repos["accounts"].find_many.return_value = [
            {"account_name": "유동자산-현금", "account_type": "asset", "is_current": True},
            {"account_name": "유동자산-매출채권", "account_type": "asset", "is_current": True},
            {"account_name": "비유동자산-건물", "account_type": "asset", "is_current": False},
            {"account_name": "유동부채-매입채무", "account_type": "liability", "is_current": True},
            {"account_name": "비유동부채-차입금", "account_type": "liability", "is_current": False},
            {"account_name": "자본금", "account_type": "equity"},
            {"account_name": "매출", "account_type": "income"},
            {"account_name": "매출원가", "account_type": "expense"},
        ]

        # 분개전표:
        # 유동자산: 현금 100M + 매출채권 100M = 200M
        # 비유동자산: 건물 200M
        # 유동부채: 매입채무 80M
        # 비유동부채: 차입금 100M
        # 자본금: 120M
        # 매출 100M, 매출원가 70M -> 순이익 30M
        repos["journal_entries"].find_many.return_value = [
            {
                "_id": "JE-001",
                "docstatus": 1,
                "items": [
                    {
                        "account": "유동자산-현금",
                        "account_type": "asset",
                        "debit": Decimal(100000000),
                        "credit": Decimal(0),
                    },
                    {
                        "account": "유동자산-매출채권",
                        "account_type": "asset",
                        "debit": Decimal(100000000),
                        "credit": Decimal(0),
                    },
                    {
                        "account": "비유동자산-건물",
                        "account_type": "asset",
                        "debit": Decimal(200000000),
                        "credit": Decimal(0),
                    },
                    {
                        "account": "유동부채-매입채무",
                        "account_type": "liability",
                        "debit": Decimal(0),
                        "credit": Decimal(80000000),
                    },
                    {
                        "account": "비유동부채-차입금",
                        "account_type": "liability",
                        "debit": Decimal(0),
                        "credit": Decimal(100000000),
                    },
                    {
                        "account": "자본금",
                        "account_type": "equity",
                        "debit": Decimal(0),
                        "credit": Decimal(120000000),
                    },
                    {
                        "account": "매출",
                        "account_type": "income",
                        "debit": Decimal(0),
                        "credit": Decimal(100000000),
                    },
                    {
                        "account": "매출원가",
                        "account_type": "expense",
                        "debit": Decimal(70000000),
                        "credit": Decimal(0),
                    },
                ],
            }
        ]

        result = service.analyze_ratios(
            period_start=date(2026, 1, 1),
            period_end=date(2026, 4, 10),
        )

        # 합산:
        # 총자산 = 400M, 유동자산 = 200M
        # 총부채 = 180M, 유동부채 = 80M
        # 자기자본 = 120M
        # 당기순이익 = 100M - 70M = 30M
        snapshot = result["snapshot"]
        assert snapshot["total_assets"] == Decimal(400000000)
        assert snapshot["current_assets"] == Decimal(200000000)
        assert snapshot["total_liabilities"] == Decimal(180000000)
        assert snapshot["current_liabilities"] == Decimal(80000000)
        assert snapshot["total_equity"] == Decimal(120000000)
        assert snapshot["net_income"] == Decimal(30000000)

        ratios = result["ratios"]
        # 유동비율 = 200M/80M = 2.50
        assert ratios["current_ratio"] == Decimal("2.50")
        # 부채비율 = 180/120 x 100 = 150
        assert ratios["debt_ratio"] == Decimal("150.00")
        # 자기자본비율 = 120/400 x 100 = 30.00
        assert ratios["equity_ratio"] == Decimal("30.00")
        # ROA = 30/400 x 100 = 7.50
        assert ratios["roa"] == Decimal("7.50")
        # ROE = 30/120 x 100 = 25.00
        assert ratios["roe"] == Decimal("25.00")

    def test_데이터_없으면_모든_비율_None(self) -> None:
        """전표가 없으면 모든 합계가 0이고 비율은 None."""
        service, repos = _make_service()
        repos["accounts"].find_many.return_value = []
        repos["journal_entries"].find_many.return_value = []

        result = service.analyze_ratios(
            period_start=date(2026, 1, 1),
            period_end=date(2026, 4, 10),
        )

        snapshot = result["snapshot"]
        assert snapshot["total_assets"] == Decimal(0)
        assert snapshot["total_equity"] == Decimal(0)

        ratios = result["ratios"]
        assert ratios["current_ratio"] is None
        assert ratios["debt_ratio"] is None
        assert ratios["roa"] is None
        assert ratios["roe"] is None


class Test재무비율_보고서_저장:
    """save_ratio_report 테스트."""

    def test_분석_결과를_FinancialRatioReport_문서로_저장(self) -> None:
        service, repos = _make_service()
        repos["accounts"].find_many.return_value = [
            {"account_name": "현금", "account_type": "asset", "is_current": True},
            {"account_name": "매입채무", "account_type": "liability", "is_current": True},
            {"account_name": "자본금", "account_type": "equity"},
            {"account_name": "매출", "account_type": "income"},
        ]
        repos["journal_entries"].find_many.return_value = [
            {
                "_id": "JE-001",
                "docstatus": 1,
                "items": [
                    {
                        "account": "현금",
                        "account_type": "asset",
                        "debit": Decimal(100000000),
                        "credit": Decimal(0),
                    },
                    {
                        "account": "매입채무",
                        "account_type": "liability",
                        "debit": Decimal(0),
                        "credit": Decimal(40000000),
                    },
                    {
                        "account": "자본금",
                        "account_type": "equity",
                        "debit": Decimal(0),
                        "credit": Decimal(60000000),
                    },
                    {
                        "account": "매출",
                        "account_type": "income",
                        "debit": Decimal(0),
                        "credit": Decimal(30000000),
                    },
                ],
            }
        ]
        repos["financial_ratio_reports"].insert.return_value = "FRR-001"

        with patch(
            "oneerp_accounting_app.services.financial_ratio_service.generate_name",
            return_value="FRR-001",
        ):
            report_id = service.save_ratio_report(
                report_name="2026 1분기 재무비율",
                period_start=date(2026, 1, 1),
                period_end=date(2026, 3, 31),
            )

        assert report_id == "FRR-001"
        repos["financial_ratio_reports"].insert.assert_called_once()

        # 저장된 문서 검증
        doc = repos["financial_ratio_reports"].insert.call_args[0][0]
        assert doc.report_name == "2026 1분기 재무비율"
        assert doc.current_ratio == Decimal("2.50")  # 100M / 40M
        assert doc.roa == Decimal("30.00")  # 30M / 100M x 100
