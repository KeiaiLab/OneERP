"""원천징수 서비스(WithholdingTaxService) 단위 테스트.

한국 세법 원천징수 세율 (2026년 기준):
- 사업소득: 3% + 지방소득세 0.3% = 3.3%
- 기타소득: 필요경비 60% 공제 후 20% + 지방세 2% = 실효 8.8% (일반)
- 이자소득: 14% + 지방세 1.4% = 15.4%
- 배당소득: 14% + 지방세 1.4% = 15.4%
- 근로소득(간이세액표 별도 — 본 서비스 범위 외)
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """WithholdingTaxService와 모킹된 Repository를 반환한다."""
    with patch(
        "oneerp_accounting_app.services.withholding_tax_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.withholding_tax_service import WithholdingTaxService

        service = WithholdingTaxService(tenant_id="test-tenant")

    return service, repos


class Test사업소득_원천징수:
    """calculate_business_income 테스트 (3.3%)."""

    def test_100만원_사업소득_원천세_33000원(self) -> None:
        """사업소득 1,000,000원 -> 소득세 30,000 + 지방세 3,000 = 33,000."""
        service, _ = _make_service()

        result = service.calculate_business_income(Decimal(1000000))

        assert result["income_tax"] == Decimal(30000)
        assert result["local_income_tax"] == Decimal(3000)
        assert result["total_withholding"] == Decimal(33000)
        assert result["net_payment"] == Decimal(967000)

    def test_지급액_0원은_원천세_0원(self) -> None:
        """지급액 0원이면 원천세도 0원."""
        service, _ = _make_service()

        result = service.calculate_business_income(Decimal(0))

        assert result["total_withholding"] == Decimal(0)
        assert result["net_payment"] == Decimal(0)

    def test_음수_지급액은_예외(self) -> None:
        """음수 지급액은 거부된다."""
        service, _ = _make_service()

        with pytest.raises(ValueError, match="지급액은 0 이상"):
            service.calculate_business_income(Decimal(-1000))

    def test_원_단위_절사(self) -> None:
        """소득세·지방세는 10원 미만 절사 (국세기본법 제47조의2)."""
        service, _ = _make_service()

        # 123,457원 x 3% = 3,703.71 -> 3,700 (10원 미만 절사)
        result = service.calculate_business_income(Decimal(123457))

        assert result["income_tax"] == Decimal(3700)
        # 지방세 370 -> 370
        assert result["local_income_tax"] == Decimal(370)


class Test기타소득_원천징수:
    """calculate_other_income 테스트 (일반 기타소득 8.8% 실효세율)."""

    def test_100만원_기타소득_필요경비_60퍼센트_공제(self) -> None:
        """
        기타소득 1,000,000원:
        - 필요경비 600,000 (60%)
        - 과세표준 400,000
        - 소득세 80,000 (20%)
        - 지방세 8,000 (2%)
        - 총 원천세 88,000 (실효 8.8%)
        """
        service, _ = _make_service()

        result = service.calculate_other_income(Decimal(1000000))

        assert result["necessary_expense"] == Decimal(600000)
        assert result["taxable_amount"] == Decimal(400000)
        assert result["income_tax"] == Decimal(80000)
        assert result["local_income_tax"] == Decimal(8000)
        assert result["total_withholding"] == Decimal(88000)
        assert result["net_payment"] == Decimal(912000)

    def test_필요경비율_사용자지정(self) -> None:
        """필요경비율을 직접 지정할 수 있다 (예: 주식매매차익 0%)."""
        service, _ = _make_service()

        result = service.calculate_other_income(
            Decimal(1000000),
            necessary_expense_rate=Decimal(0),
        )

        # 과세표준 = 1,000,000 x 100% = 1,000,000
        assert result["taxable_amount"] == Decimal(1000000)
        assert result["income_tax"] == Decimal(200000)  # 20%
        assert result["local_income_tax"] == Decimal(20000)  # 2%

    def test_비과세_기준_이하_원천세_면제(self) -> None:
        """
        소액 기타소득 (과세표준 5만원 이하)은 비과세.
        10만원 x 60% 경비 = 4만원 과세표준 -> 비과세.
        """
        service, _ = _make_service()

        result = service.calculate_other_income(Decimal(100000))

        assert result["total_withholding"] == Decimal(0)
        assert result["is_tax_exempt"] is True


class Test이자_배당소득_원천징수:
    """calculate_interest_income / calculate_dividend_income 테스트 (15.4%)."""

    def test_이자소득_100만원_15_4퍼센트_원천세(self) -> None:
        """이자 1,000,000 -> 소득세 140,000 + 지방세 14,000 = 154,000."""
        service, _ = _make_service()

        result = service.calculate_interest_income(Decimal(1000000))

        assert result["income_tax"] == Decimal(140000)
        assert result["local_income_tax"] == Decimal(14000)
        assert result["total_withholding"] == Decimal(154000)

    def test_배당소득_100만원_15_4퍼센트_원천세(self) -> None:
        service, _ = _make_service()

        result = service.calculate_dividend_income(Decimal(1000000))

        assert result["income_tax"] == Decimal(140000)
        assert result["local_income_tax"] == Decimal(14000)
        assert result["total_withholding"] == Decimal(154000)


class Test원천징수_분개_자동생성:
    """create_withholding_journal 테스트."""

    def test_사업소득_지급_분개_3라인(self) -> None:
        """
        용역비 1,000,000 지급 시:
        차변: 지급수수료 1,000,000
        대변: 예수금-소득세 30,000
        대변: 예수금-지방소득세 3,000
        대변: 현금 967,000
        """
        service, repos = _make_service()
        repos["journal_entries"].insert.return_value = "JE-WHT-001"

        with patch(
            "oneerp_accounting_app.services.withholding_tax_service.generate_name",
            return_value="JE-WHT-001",
        ):
            je_id = service.create_withholding_journal(
                payment_amount=Decimal(1000000),
                income_type="business",
                expense_account="지급수수료",
                cash_account="현금",
                party="프리랜서 김철수",
                posting_date="2026-04-10",
            )

        assert je_id == "JE-WHT-001"
        repos["journal_entries"].insert.assert_called_once()

        # 분개 내용 검증
        je_doc = repos["journal_entries"].insert.call_args[0][0]
        items = je_doc.items if hasattr(je_doc, "items") else je_doc["items"]

        # 차변 합계 = 대변 합계 검증
        total_debit = sum(
            Decimal(str(i.debit if hasattr(i, "debit") else i["debit"])) for i in items
        )
        total_credit = sum(
            Decimal(str(i.credit if hasattr(i, "credit") else i["credit"])) for i in items
        )
        assert total_debit == total_credit == Decimal(1000000)
        # 4개 라인: 비용, 예수금-소득세, 예수금-지방세, 현금
        assert len(items) == 4

    def test_지급액_0원은_분개_생성하지_않음(self) -> None:
        """지급액이 0이면 빈 분개를 만들지 않는다."""
        service, _repos = _make_service()

        with pytest.raises(ValueError, match="지급액"):
            service.create_withholding_journal(
                payment_amount=Decimal(0),
                income_type="business",
                expense_account="지급수수료",
                cash_account="현금",
                party="미지급",
                posting_date="2026-04-10",
            )


class Test원천세_종합_계산:
    """calculate_withholding (소득유형 파라미터 기반 디스패처) 테스트."""

    def test_소득유형_business_분기(self) -> None:
        service, _ = _make_service()

        result = service.calculate_withholding(
            payment_amount=Decimal(1000000),
            income_type="business",
        )

        assert result["total_withholding"] == Decimal(33000)

    def test_소득유형_other_분기(self) -> None:
        service, _ = _make_service()

        result = service.calculate_withholding(
            payment_amount=Decimal(1000000),
            income_type="other",
        )

        assert result["total_withholding"] == Decimal(88000)

    def test_소득유형_interest_분기(self) -> None:
        service, _ = _make_service()

        result = service.calculate_withholding(
            payment_amount=Decimal(1000000),
            income_type="interest",
        )

        assert result["total_withholding"] == Decimal(154000)

    def test_알려지지_않은_소득유형_예외(self) -> None:
        service, _ = _make_service()

        with pytest.raises(ValueError, match="지원하지 않는 소득 유형"):
            service.calculate_withholding(
                payment_amount=Decimal(1000000),
                income_type="unknown",
            )
