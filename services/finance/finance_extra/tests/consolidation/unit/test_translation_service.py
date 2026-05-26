"""통화 환산 서비스(TranslationService) 단위 테스트.

BR-CSL-003: 통화 환산 규칙
BR-CSL-004: NCI 배분 비율
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_finance_extra_app.consolidation.services.translation_service import TranslationService


def _make_service() -> TranslationService:
    """TranslationService 인스턴스를 반환한다."""
    return TranslationService()


class Test통화환산:
    """BR-CSL-003: K-IFRS 제1021호 환산 규칙 테스트."""

    def test_BS자산_기말환율(self) -> None:
        """현금(자산) $1,000,000 x 기말 1,350 = 1,350,000,000원."""
        svc = _make_service()
        result = svc.translate_bs_item(Decimal(1000000), Decimal(1350))
        assert result == Decimal(1350000000)

    def test_BS부채_기말환율(self) -> None:
        """차입금(부채) $500,000 x 기말 1,350 = 675,000,000원."""
        svc = _make_service()
        result = svc.translate_bs_item(Decimal(500000), Decimal(1350))
        assert result == Decimal(675000000)

    def test_BS자본_역사적환율(self) -> None:
        """자본금 $200,000 x 역사적 1,180 = 236,000,000원."""
        svc = _make_service()
        result = svc.translate_equity_item(Decimal(200000), Decimal(1180))
        assert result == Decimal(236000000)

    def test_PL매출_평균환율(self) -> None:
        """매출 $2,000,000 x 평균 1,340 = 2,680,000,000원."""
        svc = _make_service()
        result = svc.translate_pl_item(Decimal(2000000), Decimal(1340))
        assert result == Decimal(2680000000)

    def test_PL비용_평균환율(self) -> None:
        """비용 $1,800,000 x 평균 1,340 = 2,412,000,000원."""
        svc = _make_service()
        result = svc.translate_pl_item(Decimal(1800000), Decimal(1340))
        assert result == Decimal(2412000000)

    def test_JPY_환산_기말(self) -> None:
        """L3 SC-CSL-004: 총자산 JPY 1,200,000,000 x 9.05 = 10,860,000,000원."""
        svc = _make_service()
        result = svc.translate_bs_item(Decimal(1200000000), Decimal("9.05"))
        assert result == Decimal("10860000000.00")

    def test_JPY_환산_평균(self) -> None:
        """당기순이익 JPY 100,000,000 x 9.00 = 900,000,000원."""
        svc = _make_service()
        result = svc.translate_pl_item(Decimal(100000000), Decimal("9.00"))
        assert result == Decimal("900000000.00")


class TestNCI배분:
    """BR-CSL-004: NCI 배분 비율 테스트."""

    def test_직접소유_80퍼센트(self) -> None:
        """유효 지분율 80% → NCI 20%."""
        svc = _make_service()
        result = svc.calculate_nci_allocation(
            effective_ownership_percentage=Decimal(80),
            net_income=Decimal(1000000000),
            net_assets=Decimal(5000000000),
        )
        assert result["nci_percentage"] == Decimal(20)
        assert result["nci_profit"] == Decimal(200000000)
        assert result["nci_equity"] == Decimal(1000000000)

    def test_직접소유_60퍼센트(self) -> None:
        """유효 지분율 60% → NCI 40%."""
        svc = _make_service()
        result = svc.calculate_nci_allocation(
            effective_ownership_percentage=Decimal(60),
            net_income=Decimal(500000000),
            net_assets=Decimal(3000000000),
        )
        assert result["nci_percentage"] == Decimal(40)
        assert result["nci_profit"] == Decimal(200000000)

    def test_완전소유_NCI없음(self) -> None:
        """유효 지분율 100% → NCI 0%."""
        svc = _make_service()
        result = svc.calculate_nci_allocation(
            effective_ownership_percentage=Decimal(100),
            net_income=Decimal(800000000),
            net_assets=Decimal(4000000000),
        )
        assert result["nci_percentage"] == Decimal(0)
        assert result["nci_profit"] == Decimal(0)

    def test_간접소유_56퍼센트(self) -> None:
        """유효 지분율 56% (70%x80%) → NCI 44%."""
        svc = _make_service()
        result = svc.calculate_nci_allocation(
            effective_ownership_percentage=Decimal(56),
            net_income=Decimal(300000000),
            net_assets=Decimal(2000000000),
        )
        assert result["nci_percentage"] == Decimal(44)
        assert result["nci_profit"] == Decimal(132000000)

    def test_OCI_배분(self) -> None:
        """기타포괄손익도 NCI 비율로 배분."""
        svc = _make_service()
        result = svc.calculate_nci_allocation(
            effective_ownership_percentage=Decimal(80),
            net_income=Decimal(1000000000),
            net_assets=Decimal(5000000000),
            oci=Decimal(100000000),
        )
        assert result["nci_oci"] == Decimal(20000000)


class TestFCTA산출:
    """FCTA(해외사업환산손익) 산출 테스트."""

    def test_기본_FCTA(self) -> None:
        """BS 기말 - 자본 역사적 - PL 평균으로 FCTA 산출."""
        svc = _make_service()
        result = svc.calculate_fcta(
            bs_total_closing=Decimal(10000000000),
            pl_total_average=Decimal(1000000000),
            equity_total_historical=Decimal(8500000000),
        )
        # 100억 - 85억 - 10억 = 5억
        expected_current = Decimal(500000000)
        assert result["current_fcta"] == expected_current
        assert result["closing_fcta"] == expected_current

    def test_FCTA_기초잔액_포함(self) -> None:
        """기초 FCTA 잔액이 있는 경우."""
        svc = _make_service()
        result = svc.calculate_fcta(
            bs_total_closing=Decimal(10000000000),
            pl_total_average=Decimal(1000000000),
            equity_total_historical=Decimal(8500000000),
            opening_fcta=Decimal(200000000),
        )
        assert result["current_fcta"] == Decimal(500000000)
        assert result["closing_fcta"] == Decimal(700000000)
