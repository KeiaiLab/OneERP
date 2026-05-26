"""지분법 서비스(EquityMethodService) 단위 테스트.

BR-CSL-014: 지분법 손익 인식 (관계기업/공동기업)
BR-CSL-016: 유효 지분율 계산 (직접 + 간접)
K-IFRS 제1028호 "관계기업과 공동기업에 대한 투자"

검증 포인트:
- 지분법 손익 = 피투자자 당기순이익 x 지분율
- 투자자산 장부가액 = 취득원가 + sum(누적 지분법 손익) + sum(누적 OCI) - sum(배당)
- 유효 지분율 = 직접 + sum(중간법인 유효 지분율 x 중간법인 -> 피투자자 지분율)
- 손상검사: 장부가액 > 회수가능액이면 손실 인식
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from oneerp_finance_extra_app.consolidation.services.equity_method_service import (
    EquityMethodService,
)


class Test지분법손익_BR_CSL_014:
    """BR-CSL-014: 관계기업 당기순이익 x 지분율."""

    def test_이익_인식_30퍼센트(self) -> None:
        """관계기업 당기순이익 5억 x 지분율 30% = 1억 5천만."""
        service = EquityMethodService()
        result = service.calculate_equity_income(
            investee_net_income=Decimal(500_000_000),
            ownership_percentage=Decimal(30),
        )
        assert result == Decimal(150_000_000)

    def test_손실_인식_25퍼센트(self) -> None:
        """관계기업 당기순손실 -2억 x 25% = -5천만."""
        service = EquityMethodService()
        result = service.calculate_equity_income(
            investee_net_income=Decimal(-200_000_000),
            ownership_percentage=Decimal(25),
        )
        assert result == Decimal(-50_000_000)

    def test_지분율_0_손익_0(self) -> None:
        """지분율 0 -> 손익 0."""
        service = EquityMethodService()
        assert service.calculate_equity_income(
            investee_net_income=Decimal(1_000_000_000),
            ownership_percentage=Decimal(0),
        ) == Decimal(0)


class Test투자자산_장부가액_BR_CSL_014:
    """BR-CSL-014: 투자자산 장부가액 변동 (지분법 손익/OCI/배당 반영)."""

    def test_취득원가_이익_가산(self) -> None:
        """10억 취득 -> 누적 지분법 손익 1.5억 -> 장부가액 11.5억."""
        service = EquityMethodService()
        book_value = service.calculate_investment_book_value(
            acquisition_cost=Decimal(1_000_000_000),
            cumulative_equity_income=Decimal(150_000_000),
            cumulative_equity_oci=Decimal(0),
            cumulative_dividends_received=Decimal(0),
        )
        assert book_value == Decimal(1_150_000_000)

    def test_배당_수령_차감(self) -> None:
        """10억 취득 + 손익 4억 - 배당 2억 = 12억."""
        service = EquityMethodService()
        book_value = service.calculate_investment_book_value(
            acquisition_cost=Decimal(1_000_000_000),
            cumulative_equity_income=Decimal(400_000_000),
            cumulative_equity_oci=Decimal(0),
            cumulative_dividends_received=Decimal(200_000_000),
        )
        assert book_value == Decimal(1_200_000_000)

    def test_OCI_가산(self) -> None:
        """OCI 5천만 추가."""
        service = EquityMethodService()
        book_value = service.calculate_investment_book_value(
            acquisition_cost=Decimal(1_000_000_000),
            cumulative_equity_income=Decimal(100_000_000),
            cumulative_equity_oci=Decimal(50_000_000),
            cumulative_dividends_received=Decimal(0),
        )
        assert book_value == Decimal(1_150_000_000)

    def test_손실_누적(self) -> None:
        """취득 10억 + 누적손실 -3억 -> 7억."""
        service = EquityMethodService()
        book_value = service.calculate_investment_book_value(
            acquisition_cost=Decimal(1_000_000_000),
            cumulative_equity_income=Decimal(-300_000_000),
            cumulative_equity_oci=Decimal(0),
            cumulative_dividends_received=Decimal(0),
        )
        assert book_value == Decimal(700_000_000)


class Test유효지분율_BR_CSL_016:
    """BR-CSL-016: 유효 지분율 계산 (직접 + 간접)."""

    def test_직접소유_80퍼센트(self) -> None:
        """P->S: 80%, 간접 경로 없음 -> 80%."""
        service = EquityMethodService()
        relations = [
            {"investor": "P", "investee": "S", "ownership": Decimal(80)},
        ]
        rate = service.calculate_effective_ownership(
            relations=relations,
            parent_entity="P",
            target_entity="S",
        )
        assert rate == Decimal(80)

    def test_간접소유_70_80_56(self) -> None:
        """P->M: 70%, M->S: 80% -> 56%."""
        service = EquityMethodService()
        relations = [
            {"investor": "P", "investee": "M", "ownership": Decimal(70)},
            {"investor": "M", "investee": "S", "ownership": Decimal(80)},
        ]
        rate = service.calculate_effective_ownership(
            relations=relations,
            parent_entity="P",
            target_entity="S",
        )
        assert rate == Decimal(56)

    def test_직접_간접_혼합(self) -> None:
        """P->S: 10%, P->M: 70%, M->S: 80% -> 10 + 56 = 66%."""
        service = EquityMethodService()
        relations = [
            {"investor": "P", "investee": "S", "ownership": Decimal(10)},
            {"investor": "P", "investee": "M", "ownership": Decimal(70)},
            {"investor": "M", "investee": "S", "ownership": Decimal(80)},
        ]
        rate = service.calculate_effective_ownership(
            relations=relations,
            parent_entity="P",
            target_entity="S",
        )
        assert rate == Decimal(66)

    def test_경로_없음_0(self) -> None:
        """연결 경로 없으면 0."""
        service = EquityMethodService()
        relations = [
            {"investor": "X", "investee": "Y", "ownership": Decimal(50)},
        ]
        rate = service.calculate_effective_ownership(
            relations=relations,
            parent_entity="P",
            target_entity="S",
        )
        assert rate == Decimal(0)


class Test지분법손상_K_IFRS_1028:
    """K-IFRS 1028 손상 검토: 장부가액 > 회수가능액 -> 손상차손."""

    def test_손상차손_인식(self) -> None:
        """장부가 12억, 회수가능 10억 -> 손상차손 2억."""
        service = EquityMethodService()
        result = service.test_impairment(
            book_value=Decimal(1_200_000_000),
            recoverable_amount=Decimal(1_000_000_000),
        )
        assert result["impaired"] is True
        assert result["impairment_loss"] == Decimal(200_000_000)

    def test_손상없음(self) -> None:
        """장부가 10억 < 회수가능 11억 -> 손상 없음."""
        service = EquityMethodService()
        result = service.test_impairment(
            book_value=Decimal(1_000_000_000),
            recoverable_amount=Decimal(1_100_000_000),
        )
        assert result["impaired"] is False
        assert result["impairment_loss"] == Decimal(0)

    def test_지분법_손실_0이하_중단(self) -> None:
        """지분법 적용 후 투자장부가 ≤ 0이면 추가 손실 인식 중단(K-IFRS 1028.38)."""
        service = EquityMethodService()
        # 취득 2억, 누적 손실 -2.5억 -> 장부가 -5천만 -> 0으로 제한
        book_value = service.calculate_investment_book_value(
            acquisition_cost=Decimal(200_000_000),
            cumulative_equity_income=Decimal(-250_000_000),
            cumulative_equity_oci=Decimal(0),
            cumulative_dividends_received=Decimal(0),
            floor_at_zero=True,
        )
        assert book_value == Decimal(0)


class Test지분법_시나리오_통합:
    """통합 시나리오: L2 예시 3 (이익 + 배당)."""

    def test_L2_예시3_이익과_배당(self) -> None:
        """관계기업 순이익 10억, 지분율 40%, 배당 2억 수령.

        지분법 손익 = 4억
        장부가액 변동 = 4억 - 2억 = +2억
        """
        service = EquityMethodService()

        equity_income = service.calculate_equity_income(
            investee_net_income=Decimal(1_000_000_000),
            ownership_percentage=Decimal(40),
        )
        assert equity_income == Decimal(400_000_000)

        # 누적 기준 장부가
        initial_cost = Decimal(2_000_000_000)
        new_book = service.calculate_investment_book_value(
            acquisition_cost=initial_cost,
            cumulative_equity_income=equity_income,
            cumulative_equity_oci=Decimal(0),
            cumulative_dividends_received=Decimal(200_000_000),
        )
        # 20억 + 4억 - 2억 = 22억
        assert new_book == Decimal(2_200_000_000)


@pytest.mark.parametrize(
    ("net_income", "rate", "expected"),
    [
        (Decimal(500_000_000), Decimal(30), Decimal(150_000_000)),
        (Decimal(300_000_000), Decimal(20), Decimal(60_000_000)),
        (Decimal(-100_000_000), Decimal(40), Decimal(-40_000_000)),
    ],
)
def test_지분법손익_파라미터라이즈(net_income: Decimal, rate: Decimal, expected: Decimal) -> None:
    """여러 케이스 병렬 검증."""
    service = EquityMethodService()
    assert service.calculate_equity_income(net_income, rate) == expected
