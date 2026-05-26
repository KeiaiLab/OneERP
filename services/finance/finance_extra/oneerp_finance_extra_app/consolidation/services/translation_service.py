"""통화 환산 서비스 — K-IFRS 제1021호 환산 규칙, FCTA 산출.

L2 비즈니스 룰 매핑:
- BR-CSL-003: 통화 환산 규칙 (BS 기말/PL 평균/자본 역사적)
- BR-CSL-004: NCI 배분 비율
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


class TranslationService:
    """통화 환산 비즈니스 로직."""

    def translate_amount(
        self,
        original_amount: Decimal,
        rate: Decimal,
    ) -> Decimal:
        """금액을 환율로 환산한다.

        Args:
            original_amount: 원통화 금액
            rate: 적용 환율

        Returns:
            환산 후 금액
        """
        return original_amount * rate

    def translate_bs_item(
        self,
        original_amount: Decimal,
        closing_rate: Decimal,
    ) -> Decimal:
        """BR-CSL-003: BS 자산/부채 환산 (기말 환율).

        Args:
            original_amount: 원통화 금액
            closing_rate: 기말 환율

        Returns:
            환산 후 금액
        """
        return original_amount * closing_rate

    def translate_pl_item(
        self,
        original_amount: Decimal,
        average_rate: Decimal,
    ) -> Decimal:
        """BR-CSL-003: PL 수익/비용 환산 (평균 환율).

        Args:
            original_amount: 원통화 금액
            average_rate: 평균 환율

        Returns:
            환산 후 금액
        """
        return original_amount * average_rate

    def translate_equity_item(
        self,
        original_amount: Decimal,
        historical_rate: Decimal,
    ) -> Decimal:
        """BR-CSL-003: BS 자본 환산 (역사적 환율).

        Args:
            original_amount: 원통화 금액
            historical_rate: 역사적 환율

        Returns:
            환산 후 금액
        """
        return original_amount * historical_rate

    def calculate_nci_allocation(
        self,
        effective_ownership_percentage: Decimal,
        net_income: Decimal,
        net_assets: Decimal,
        oci: Decimal = Decimal(0),
    ) -> dict[str, Any]:
        """BR-CSL-004: NCI 배분 비율 및 금액 산출.

        Args:
            effective_ownership_percentage: 유효 지분율 (%)
            net_income: 종속기업 당기순이익
            net_assets: 종속기업 순자산
            oci: 기타포괄손익

        Returns:
            nci_percentage, nci_profit, nci_equity, nci_oci 딕셔너리
        """
        nci_rate = Decimal(1) - effective_ownership_percentage / Decimal(100)

        return {
            "nci_percentage": nci_rate * Decimal(100),
            "nci_profit": net_income * nci_rate,
            "nci_equity": net_assets * nci_rate,
            "nci_oci": oci * nci_rate,
        }

    def calculate_fcta(
        self,
        bs_total_closing: Decimal,
        pl_total_average: Decimal,
        equity_total_historical: Decimal,
        opening_fcta: Decimal = Decimal(0),
    ) -> dict[str, Decimal]:
        """FCTA(해외사업환산손익) 산출.

        BS 기말 환율 적용 합계와 PL 평균 환율 + 자본 역사적 환율
        합계의 차이로 당기 FCTA를 산출한다.

        Returns:
            current_fcta, closing_fcta 딕셔너리
        """
        # FCTA = BS 순자산(기말환율) - 자본(역사적) - PL(평균)
        current_fcta = bs_total_closing - equity_total_historical - pl_total_average
        closing_fcta = opening_fcta + current_fcta

        return {
            "current_fcta": current_fcta,
            "closing_fcta": closing_fcta,
        }
