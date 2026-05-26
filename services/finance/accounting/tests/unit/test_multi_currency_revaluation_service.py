"""다통화 재평가 서비스(MultiCurrencyRevaluationService) 단위 테스트.

테스트 대상 비즈니스 룰:
- BR-ADV-ACC-014: 화폐성 항목만 재평가 (외화 채권/채무/예금/차입금)
- BR-ADV-ACC-015: 재평가 분개 역분개 (취소 시)
- IAS 21.23: 화폐성 항목은 보고일 종가환율로 환산
- 외환차손익은 P&L에 인식 (limited 예외 외)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """MultiCurrencyRevaluationService와 모킹된 Repository를 반환한다."""
    with patch(
        "oneerp_accounting_app.services.multi_currency_revaluation_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.multi_currency_revaluation_service import (
            MultiCurrencyRevaluationService,
        )

        service = MultiCurrencyRevaluationService(tenant_id="test-tenant")

    return service, repos


class Test화폐성_비화폐성_분류:
    """is_monetary_account 정적 함수 테스트."""

    def test_자산_부채중_채권_채무_예금_차입금은_화폐성(self) -> None:
        from oneerp_accounting_app.services.multi_currency_revaluation_service import (
            is_monetary_account,
        )

        # 화폐성 항목
        assert is_monetary_account("외화 매출채권", "asset") is True
        assert is_monetary_account("외화 매입채무", "liability") is True
        assert is_monetary_account("외화 보통예금", "asset") is True
        assert is_monetary_account("외화 차입금", "liability") is True
        assert is_monetary_account("외화 미수금", "asset") is True
        assert is_monetary_account("외화 미지급금", "liability") is True

    def test_재고자산_유형자산은_비화폐성(self) -> None:
        from oneerp_accounting_app.services.multi_currency_revaluation_service import (
            is_monetary_account,
        )

        assert is_monetary_account("외화 재고자산", "asset") is False
        assert is_monetary_account("외화 건물", "asset") is False
        assert is_monetary_account("외화 토지", "asset") is False
        assert is_monetary_account("외화 선급금", "asset") is False  # 비화폐성

    def test_수익_비용_자본은_재평가_대상_아님(self) -> None:
        from oneerp_accounting_app.services.multi_currency_revaluation_service import (
            is_monetary_account,
        )

        assert is_monetary_account("외화 매출", "income") is False
        assert is_monetary_account("외화 비용", "expense") is False
        assert is_monetary_account("외화 자본금", "equity") is False


class Test환율차이_계산:
    """calculate_revaluation_diff 정적 함수 테스트."""

    def test_USD_채권_환율_상승시_평가이익(self) -> None:
        """USD 1,000 외화채권, 장부=1,300원/USD, 종가=1,350원/USD -> 50,000 평가이익."""
        from oneerp_accounting_app.services.multi_currency_revaluation_service import (
            calculate_revaluation_diff,
        )

        result = calculate_revaluation_diff(
            foreign_amount=Decimal(1000),
            book_rate=Decimal(1300),
            closing_rate=Decimal(1350),
            account_type="asset",
        )

        assert result["foreign_amount"] == Decimal(1000)
        assert result["book_value"] == Decimal(1300000)
        assert result["new_value"] == Decimal(1350000)
        assert result["diff"] == Decimal(50000)
        assert result["is_gain"] is True

    def test_USD_채권_환율_하락시_평가손실(self) -> None:
        """USD 1,000 외화채권, 장부=1,300, 종가=1,250 -> 50,000 평가손실."""
        from oneerp_accounting_app.services.multi_currency_revaluation_service import (
            calculate_revaluation_diff,
        )

        result = calculate_revaluation_diff(
            foreign_amount=Decimal(1000),
            book_rate=Decimal(1300),
            closing_rate=Decimal(1250),
            account_type="asset",
        )

        assert result["diff"] == Decimal(-50000)
        assert result["is_gain"] is False

    def test_USD_부채_환율_상승시_평가손실(self) -> None:
        """
        외화 부채(매입채무) 1,000 USD, 장부=1,300, 종가=1,350.
        부채는 환율 상승 시 갚을 금액 증가 -> 평가손실.
        """
        from oneerp_accounting_app.services.multi_currency_revaluation_service import (
            calculate_revaluation_diff,
        )

        result = calculate_revaluation_diff(
            foreign_amount=Decimal(1000),
            book_rate=Decimal(1300),
            closing_rate=Decimal(1350),
            account_type="liability",
        )

        # 부채 평가차이는 부호 반전
        assert result["diff"] == Decimal(-50000)
        assert result["is_gain"] is False


class Test다통화_일괄_재평가:
    """run_revaluation 테스트."""

    def test_USD_KRW_복수_계정_재평가_요약(self) -> None:
        """3개 외화 계정을 USD/KRW 환율로 재평가 -> 총 손익 산출."""
        service, _repos = _make_service()

        # 외화 계정 설정 (account_balances는 통합 입력 형태로 제공)
        balances = [
            {
                "account": "외화 매출채권",
                "account_type": "asset",
                "currency": "USD",
                "foreign_amount": Decimal(10000),
                "book_rate": Decimal(1300),
            },
            {
                "account": "외화 매입채무",
                "account_type": "liability",
                "currency": "USD",
                "foreign_amount": Decimal(5000),
                "book_rate": Decimal(1300),
            },
            {
                "account": "외화 재고자산",  # 비화폐성 - 제외
                "account_type": "asset",
                "currency": "USD",
                "foreign_amount": Decimal(8000),
                "book_rate": Decimal(1300),
            },
        ]

        result = service.run_revaluation(
            revaluation_date=date(2026, 4, 30),
            base_currency="KRW",
            closing_rates={"USD": Decimal(1350)},
            account_balances=balances,
        )

        # 화폐성 자산 (매출채권): 1,350 - 1,300 = 50 x 10,000 = 500,000 이익
        # 화폐성 부채 (매입채무): 평가손실 = -50 x 5,000 = -250,000
        # 비화폐성(재고): 제외
        # 순손익 = 500,000 - 250,000 = 250,000
        assert result["base_currency"] == "KRW"
        assert result["accounts_revalued"] == 2  # 화폐성 2개만
        assert result["total_gain_loss"] == Decimal(250000)
        assert result["total_gain"] == Decimal(500000)
        assert result["total_loss"] == Decimal(250000)
        assert len(result["details"]) == 2

    def test_환율_누락된_통화는_건너뜀(self) -> None:
        """closing_rates에 없는 통화는 처리하지 않고 skipped로 분류."""
        service, _repos = _make_service()

        balances = [
            {
                "account": "외화 매출채권",
                "account_type": "asset",
                "currency": "EUR",  # closing_rates에 없음
                "foreign_amount": Decimal(1000),
                "book_rate": Decimal(1450),
            },
        ]

        result = service.run_revaluation(
            revaluation_date=date(2026, 4, 30),
            base_currency="KRW",
            closing_rates={"USD": Decimal(1350)},  # USD만
            account_balances=balances,
        )

        assert result["accounts_revalued"] == 0
        assert result["accounts_skipped"] == 1
        assert "EUR" in result["skipped_currencies"]

    def test_빈_입력은_손익_0원(self) -> None:
        service, _repos = _make_service()

        result = service.run_revaluation(
            revaluation_date=date(2026, 4, 30),
            base_currency="KRW",
            closing_rates={"USD": Decimal(1350)},
            account_balances=[],
        )

        assert result["accounts_revalued"] == 0
        assert result["total_gain_loss"] == Decimal(0)


class Test재평가_분개_생성:
    """generate_revaluation_journal 테스트."""

    def test_평가이익_분개_차변_채권_대변_외환차익(self) -> None:
        """USD 채권 평가이익 100,000 -> 차변: 외화매출채권 100,000, 대변: 외환차익 100,000."""
        service, repos = _make_service()
        repos["journal_entries"].insert.return_value = "JE-REV-001"

        with patch(
            "oneerp_accounting_app.services.multi_currency_revaluation_service.generate_name",
            return_value="JE-REV-001",
        ):
            je_id = service.generate_revaluation_journal(
                account="외화 매출채권",
                account_type="asset",
                diff=Decimal(100000),
                revaluation_date=date(2026, 4, 30),
                currency="USD",
            )

        assert je_id == "JE-REV-001"
        repos["journal_entries"].insert.assert_called_once()

        je_doc = repos["journal_entries"].insert.call_args[0][0]
        items = je_doc.items
        assert len(items) == 2
        # 차변 = 채권 100,000
        assert items[0].account == "외화 매출채권"
        assert items[0].debit == Decimal(100000)
        # 대변 = 외환차익 100,000
        assert items[1].account == "외환차익"
        assert items[1].credit == Decimal(100000)

    def test_평가손실_분개_차변_외환차손_대변_채권(self) -> None:
        """USD 채권 평가손실 50,000 -> 차변: 외환차손, 대변: 채권."""
        service, repos = _make_service()
        repos["journal_entries"].insert.return_value = "JE-REV-002"

        with patch(
            "oneerp_accounting_app.services.multi_currency_revaluation_service.generate_name",
            return_value="JE-REV-002",
        ):
            service.generate_revaluation_journal(
                account="외화 매출채권",
                account_type="asset",
                diff=Decimal(-50000),
                revaluation_date=date(2026, 4, 30),
                currency="USD",
            )

        je_doc = repos["journal_entries"].insert.call_args[0][0]
        items = je_doc.items
        assert items[0].account == "외환차손"
        assert items[0].debit == Decimal(50000)
        assert items[1].account == "외화 매출채권"
        assert items[1].credit == Decimal(50000)

    def test_차이_0원은_분개_생성_안함(self) -> None:
        """diff=0이면 분개 생성하지 않고 None 반환."""
        service, repos = _make_service()

        result = service.generate_revaluation_journal(
            account="외화 매출채권",
            account_type="asset",
            diff=Decimal(0),
            revaluation_date=date(2026, 4, 30),
            currency="USD",
        )

        assert result is None
        repos["journal_entries"].insert.assert_not_called()
