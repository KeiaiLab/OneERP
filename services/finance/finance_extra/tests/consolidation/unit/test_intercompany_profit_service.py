"""내부거래 이익/대여/배당 소거 서비스 단위 테스트.

BR-CSL-015: 내부배당 소거
BR-CSL-017: 고정자산 미실현이익 소거 + 감가상각 조정
BR-CSL-018: 내부대여금/차입금 소거 + 이자 소거
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from oneerp_finance_extra_app.consolidation.services.intercompany_profit_service import (
    IntercompanyProfitService,
)


class Test고정자산_미실현이익_BR_CSL_017:
    """BR-CSL-017: 고정자산 미실현이익 + 감가상각 조정."""

    def test_기본케이스_500_300_200(self) -> None:
        """매각가 5억, 장부가 3억 -> 미실현이익 2억."""
        service = IntercompanyProfitService()
        result = service.calculate_asset_unrealized_profit(
            sale_price=Decimal(500_000_000),
            seller_book_value=Decimal(300_000_000),
            remaining_useful_life_years=5,
        )
        assert result["unrealized_profit"] == Decimal(200_000_000)
        assert result["annual_depreciation_adjustment"] == Decimal(40_000_000)

    def test_장부가이전_미실현이익_0(self) -> None:
        """매각가 = 장부가 -> 미실현이익 0."""
        service = IntercompanyProfitService()
        result = service.calculate_asset_unrealized_profit(
            sale_price=Decimal(100_000_000),
            seller_book_value=Decimal(100_000_000),
            remaining_useful_life_years=10,
        )
        assert result["unrealized_profit"] == Decimal(0)
        assert result["annual_depreciation_adjustment"] == Decimal(0)

    def test_잔여내용연수_0_에러(self) -> None:
        """잔여내용연수 0 -> ValueError."""
        service = IntercompanyProfitService()
        with pytest.raises(ValueError, match="잔여 내용연수"):
            service.calculate_asset_unrealized_profit(
                sale_price=Decimal(100_000_000),
                seller_book_value=Decimal(50_000_000),
                remaining_useful_life_years=0,
            )

    def test_손실_매각시_마이너스_미실현이익(self) -> None:
        """매각가가 장부가보다 낮으면 미실현손실(음수) 반환."""
        service = IntercompanyProfitService()
        result = service.calculate_asset_unrealized_profit(
            sale_price=Decimal(300_000_000),
            seller_book_value=Decimal(500_000_000),
            remaining_useful_life_years=4,
        )
        assert result["unrealized_profit"] == Decimal(-200_000_000)
        # 연간 조정 = -2억 / 4 = -5천만
        assert result["annual_depreciation_adjustment"] == Decimal(-50_000_000)


class Test내부대여금_BR_CSL_018:
    """BR-CSL-018: 내부대여금/차입금 소거 및 이자 소거."""

    def test_원금만_소거(self) -> None:
        """대여금 10억, 이자 없음 -> 소거 10억."""
        service = IntercompanyProfitService()
        result = service.eliminate_intercompany_loan(
            principal=Decimal(1_000_000_000),
            interest_period=Decimal(0),
            interest_accrued=Decimal(0),
        )
        assert result["principal_eliminated"] == Decimal(1_000_000_000)
        assert result["interest_eliminated"] == Decimal(0)
        assert result["accrued_interest_eliminated"] == Decimal(0)
        assert result["total_eliminated"] == Decimal(1_000_000_000)

    def test_L2_예시1(self) -> None:
        """L2 예시: 원금 10억, 이자 2500만, 미수이자 8,333,333."""
        service = IntercompanyProfitService()
        result = service.eliminate_intercompany_loan(
            principal=Decimal(1_000_000_000),
            interest_period=Decimal(25_000_000),
            interest_accrued=Decimal(8333333),
        )
        assert result["principal_eliminated"] == Decimal(1_000_000_000)
        assert result["interest_eliminated"] == Decimal(25_000_000)
        assert result["accrued_interest_eliminated"] == Decimal(8333333)
        assert result["total_eliminated"] == Decimal(1033333333)

    def test_이자만_소거(self) -> None:
        """원금 0, 이자만 있는 경우."""
        service = IntercompanyProfitService()
        result = service.eliminate_intercompany_loan(
            principal=Decimal(0),
            interest_period=Decimal(5_000_000),
            interest_accrued=Decimal(0),
        )
        assert result["total_eliminated"] == Decimal(5_000_000)


class Test내부배당소거_BR_CSL_015:
    """BR-CSL-015: 내부배당 소거 + NCI 배당 배분."""

    def test_L2_예시1_80퍼센트(self) -> None:
        """배당 5억, 지분 80% -> 지배기업 수취 4억, NCI 1억."""
        service = IntercompanyProfitService()
        result = service.eliminate_intercompany_dividend(
            total_dividend=Decimal(500_000_000),
            ownership_percentage=Decimal(80),
        )
        assert result["parent_received"] == Decimal(400_000_000)
        assert result["nci_dividend"] == Decimal(100_000_000)
        assert result["elimination_amount"] == Decimal(400_000_000)

    def test_완전소유_100퍼센트(self) -> None:
        """100% 소유 -> NCI 배당 0."""
        service = IntercompanyProfitService()
        result = service.eliminate_intercompany_dividend(
            total_dividend=Decimal(1_000_000_000),
            ownership_percentage=Decimal(100),
        )
        assert result["parent_received"] == Decimal(1_000_000_000)
        assert result["nci_dividend"] == Decimal(0)

    def test_부분소유_60퍼센트(self) -> None:
        """3억 배당, 60% 소유 -> 지배기업 1.8억, NCI 1.2억."""
        service = IntercompanyProfitService()
        result = service.eliminate_intercompany_dividend(
            total_dividend=Decimal(300_000_000),
            ownership_percentage=Decimal(60),
        )
        assert result["parent_received"] == Decimal(180_000_000)
        assert result["nci_dividend"] == Decimal(120_000_000)

    def test_배당_0_결과_0(self) -> None:
        """배당 0 -> 모두 0."""
        service = IntercompanyProfitService()
        result = service.eliminate_intercompany_dividend(
            total_dividend=Decimal(0),
            ownership_percentage=Decimal(80),
        )
        assert result["parent_received"] == Decimal(0)
        assert result["nci_dividend"] == Decimal(0)
        assert result["elimination_amount"] == Decimal(0)


class Test감가상각조정_추적:
    """미실현이익 소거 이후 매 결산기마다 감가상각 조정 추적."""

    def test_연간조정_3년차_누적(self) -> None:
        """연간 조정 4천만 x 3년 = 1억 2천만 누적."""
        service = IntercompanyProfitService()
        profit_result = service.calculate_asset_unrealized_profit(
            sale_price=Decimal(500_000_000),
            seller_book_value=Decimal(300_000_000),
            remaining_useful_life_years=5,
        )
        # 매년 4천만씩 realize
        realized_3yr = profit_result["annual_depreciation_adjustment"] * Decimal(3)
        assert realized_3yr == Decimal(120_000_000)

    def test_완전상각_후_잔액_0(self) -> None:
        """잔여 5년 경과 후 미실현이익 완전 실현."""
        service = IntercompanyProfitService()
        result = service.calculate_asset_unrealized_profit(
            sale_price=Decimal(500_000_000),
            seller_book_value=Decimal(300_000_000),
            remaining_useful_life_years=5,
        )
        total_realized = result["annual_depreciation_adjustment"] * Decimal(5)
        assert total_realized == result["unrealized_profit"]
