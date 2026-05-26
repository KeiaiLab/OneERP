"""연령분석 서비스(AgedAnalysisService) 단위 테스트.

테스트 대상 비즈니스 룰:
- BR-ACCT-013: 매출채권/매입채무 연령 분류 (30/60/90/120+일)
- 한국 재무보고서 표준 연령 구간 분석
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """AgedAnalysisService와 모킹된 Repository를 반환한다."""
    with patch("oneerp_accounting_app.services.aged_analysis_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.aged_analysis_service import AgedAnalysisService

        service = AgedAnalysisService(tenant_id="test-tenant")

    return service, repos


class Test연령분류함수:
    """classify_aging_bucket 정적 함수 테스트."""

    def test_경과일_0일_이하는_미도래(self) -> None:
        """만기 전(음수/0)은 미도래 구간."""
        from oneerp_accounting_app.services.aged_analysis_service import classify_aging_bucket

        assert classify_aging_bucket(-5) == "미도래"
        assert classify_aging_bucket(0) == "미도래"

    def test_경과일_1에서_30일은_0_30_구간(self) -> None:
        """1-30일 경과는 0-30일 구간."""
        from oneerp_accounting_app.services.aged_analysis_service import classify_aging_bucket

        assert classify_aging_bucket(1) == "0-30일"
        assert classify_aging_bucket(15) == "0-30일"
        assert classify_aging_bucket(30) == "0-30일"

    def test_경과일_31에서_60일은_31_60_구간(self) -> None:
        """31-60일 경과는 31-60일 구간."""
        from oneerp_accounting_app.services.aged_analysis_service import classify_aging_bucket

        assert classify_aging_bucket(31) == "31-60일"
        assert classify_aging_bucket(60) == "31-60일"

    def test_경과일_61에서_90일은_61_90_구간(self) -> None:
        from oneerp_accounting_app.services.aged_analysis_service import classify_aging_bucket

        assert classify_aging_bucket(61) == "61-90일"
        assert classify_aging_bucket(90) == "61-90일"

    def test_경과일_91에서_120일은_91_120_구간(self) -> None:
        from oneerp_accounting_app.services.aged_analysis_service import classify_aging_bucket

        assert classify_aging_bucket(91) == "91-120일"
        assert classify_aging_bucket(120) == "91-120일"

    def test_경과일_121일_이상은_120_초과_구간(self) -> None:
        """121일 이상은 120일 초과 구간 (대손충당 후보)."""
        from oneerp_accounting_app.services.aged_analysis_service import classify_aging_bucket

        assert classify_aging_bucket(121) == "120일 초과"
        assert classify_aging_bucket(365) == "120일 초과"
        assert classify_aging_bucket(1000) == "120일 초과"


class Test매출채권연령분석:
    """analyze_receivables 테스트."""

    def test_기준일_기준_구간별_집계(self) -> None:
        """매출채권 4건을 구간별로 정확히 집계한다."""
        service, repos = _make_service()
        repos["accounts_receivable"].find_many.return_value = [
            # 미도래
            {
                "customer": "고객A",
                "outstanding_amount": Decimal(1000000),
                "due_date": date(2026, 5, 1),
                "invoice_id": "SI-001",
            },
            # 0-30일
            {
                "customer": "고객B",
                "outstanding_amount": Decimal(500000),
                "due_date": date(2026, 3, 20),
                "invoice_id": "SI-002",
            },
            # 61-90일
            {
                "customer": "고객C",
                "outstanding_amount": Decimal(300000),
                "due_date": date(2026, 1, 10),
                "invoice_id": "SI-003",
            },
            # 120일 초과
            {
                "customer": "고객D",
                "outstanding_amount": Decimal(200000),
                "due_date": date(2025, 11, 1),
                "invoice_id": "SI-004",
            },
        ]

        result = service.analyze_receivables(as_of_date=date(2026, 4, 10))

        assert result["as_of_date"] == "2026-04-10"
        assert result["total_outstanding"] == Decimal(2000000)
        assert result["buckets"]["미도래"]["amount"] == Decimal(1000000)
        assert result["buckets"]["0-30일"]["amount"] == Decimal(500000)
        assert result["buckets"]["61-90일"]["amount"] == Decimal(300000)
        assert result["buckets"]["120일 초과"]["amount"] == Decimal(200000)
        assert result["buckets"]["31-60일"]["amount"] == Decimal(0)
        assert result["buckets"]["91-120일"]["amount"] == Decimal(0)

    def test_만기일_미설정_건은_미분류(self) -> None:
        """due_date가 None이면 '미분류' 구간으로 집계한다."""
        service, repos = _make_service()
        repos["accounts_receivable"].find_many.return_value = [
            {
                "customer": "고객X",
                "outstanding_amount": Decimal(100000),
                "due_date": None,
                "invoice_id": "SI-X",
            },
        ]

        result = service.analyze_receivables(as_of_date=date(2026, 4, 10))

        assert result["buckets"]["미분류"]["amount"] == Decimal(100000)

    def test_고객별_집계_요청시_고객별_잔액_산출(self) -> None:
        """group_by_customer=True이면 고객별 합계를 반환한다."""
        service, repos = _make_service()
        repos["accounts_receivable"].find_many.return_value = [
            {
                "customer": "고객A",
                "outstanding_amount": Decimal(100000),
                "due_date": date(2026, 3, 1),
                "invoice_id": "SI-001",
            },
            {
                "customer": "고객A",
                "outstanding_amount": Decimal(200000),
                "due_date": date(2026, 2, 1),
                "invoice_id": "SI-002",
            },
            {
                "customer": "고객B",
                "outstanding_amount": Decimal(300000),
                "due_date": date(2026, 3, 15),
                "invoice_id": "SI-003",
            },
        ]

        result = service.analyze_receivables(
            as_of_date=date(2026, 4, 10),
            group_by_customer=True,
        )

        by_customer = result["by_customer"]
        assert by_customer["고객A"]["total"] == Decimal(300000)
        assert by_customer["고객B"]["total"] == Decimal(300000)

    def test_빈_데이터는_합계_0(self) -> None:
        """매출채권이 없으면 모든 구간 0원."""
        service, repos = _make_service()
        repos["accounts_receivable"].find_many.return_value = []

        result = service.analyze_receivables(as_of_date=date(2026, 4, 10))

        assert result["total_outstanding"] == Decimal(0)
        for bucket_data in result["buckets"].values():
            assert bucket_data["amount"] == Decimal(0)


class Test매입채무연령분석:
    """analyze_payables 테스트."""

    def test_기준일_기준_구간별_집계(self) -> None:
        service, repos = _make_service()
        repos["accounts_payable"].find_many.return_value = [
            {
                "supplier": "공급사A",
                "outstanding_amount": Decimal(800000),
                "due_date": date(2026, 3, 15),  # 26일 경과 -> 0-30일
                "invoice_id": "PI-001",
            },
            {
                "supplier": "공급사B",
                "outstanding_amount": Decimal(500000),
                "due_date": date(2025, 12, 1),  # 130일 경과 -> 120일 초과
                "invoice_id": "PI-002",
            },
        ]

        result = service.analyze_payables(as_of_date=date(2026, 4, 10))

        assert result["as_of_date"] == "2026-04-10"
        assert result["total_outstanding"] == Decimal(1300000)
        assert result["buckets"]["0-30일"]["amount"] == Decimal(800000)
        assert result["buckets"]["120일 초과"]["amount"] == Decimal(500000)


class Test대손충당금_추정:
    """estimate_bad_debt_provision 테스트 — BR-ACCT-013 확장."""

    def test_구간별_충당율_적용_대손충당금_산출(self) -> None:
        """기본 충당율 (0-30:0%, 31-60:1%, 61-90:5%, 91-120:20%, 120+:50%) 적용."""
        service, repos = _make_service()
        repos["accounts_receivable"].find_many.return_value = [
            # 0-30일: 1,000,000 x 0% = 0
            {
                "customer": "고객A",
                "outstanding_amount": Decimal(1000000),
                "due_date": date(2026, 3, 20),
            },
            # 91-120일: 500,000 x 20% = 100,000
            {
                "customer": "고객B",
                "outstanding_amount": Decimal(500000),
                "due_date": date(2025, 12, 20),
            },
            # 120일 초과: 200,000 x 50% = 100,000
            {
                "customer": "고객C",
                "outstanding_amount": Decimal(200000),
                "due_date": date(2025, 10, 1),
            },
        ]

        result = service.estimate_bad_debt_provision(as_of_date=date(2026, 4, 10))

        # 총 대손충당금 = 0 + 100,000 + 100,000 = 200,000
        assert result["total_provision"] == Decimal(200000)
        assert result["by_bucket"]["91-120일"] == Decimal(100000)
        assert result["by_bucket"]["120일 초과"] == Decimal(100000)

    def test_사용자_정의_충당율_적용(self) -> None:
        """커스텀 충당율(예: 보수적)을 적용할 수 있다."""
        service, repos = _make_service()
        repos["accounts_receivable"].find_many.return_value = [
            {
                "customer": "고객A",
                "outstanding_amount": Decimal(1000000),
                "due_date": date(2026, 3, 20),  # 0-30일
            },
        ]

        # 보수적 충당율: 0-30일도 2%
        custom_rates = {
            "미도래": Decimal(0),
            "0-30일": Decimal("0.02"),
            "31-60일": Decimal("0.05"),
            "61-90일": Decimal("0.10"),
            "91-120일": Decimal("0.30"),
            "120일 초과": Decimal("0.70"),
            "미분류": Decimal("0.05"),
        }

        result = service.estimate_bad_debt_provision(
            as_of_date=date(2026, 4, 10),
            provision_rates=custom_rates,
        )

        # 1,000,000 x 2% = 20,000
        assert result["total_provision"] == Decimal(20000)
