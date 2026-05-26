"""내부거래 이익/대여/배당 소거 서비스.

L2 비즈니스 룰 매핑:
- BR-CSL-015: 내부배당 소거
- BR-CSL-017: 고정자산 미실현이익 소거 및 감가상각 조정
- BR-CSL-018: 내부대여금/차입금 및 이자 소거

참조 회계 기준:
- K-IFRS 제1110호 "연결재무제표": 내부거래 완전 소거
- K-IFRS 제1028호 "관계기업과 공동기업": 관련 내부거래

설계 노트:
- 각 메서드는 순수 함수에 가깝게 설계하여 Repository 의존성 없이
  단위 테스트가 가능하다.
- 차대변 분개 템플릿은 `build_*_journal` 류 메서드에서 구성한다.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

_HUNDRED = Decimal(100)


class IntercompanyProfitService:
    """내부거래 이익/대여/배당 소거 로직."""

    def calculate_asset_unrealized_profit(
        self,
        sale_price: Decimal,
        seller_book_value: Decimal,
        remaining_useful_life_years: int,
    ) -> dict[str, Any]:
        """BR-CSL-017: 고정자산 내부매각 미실현이익 및 감가상각 조정.

        공식:
            미실현이익     = 내부매각가 - 매도법인 장부가액
            감가상각 조정   = 미실현이익 / 잔여내용연수(연)

        손실 매각의 경우 unrealized_profit이 음수가 되며, 이는 현실적으로
        드물지만 해외 자산 재평가 등에서 발생할 수 있으므로 허용한다.

        Args:
            sale_price: 그룹 내 매각 가격
            seller_book_value: 매도법인의 장부가액
            remaining_useful_life_years: 취득법인 기준 잔여 내용연수(연)

        Returns:
            unrealized_profit, annual_depreciation_adjustment 딕셔너리

        Raises:
            ValueError: 잔여 내용연수가 0 이하인 경우
        """
        if remaining_useful_life_years <= 0:
            raise ValueError("잔여 내용연수는 1년 이상이어야 합니다")

        unrealized = sale_price - seller_book_value
        annual_adj = unrealized / Decimal(remaining_useful_life_years)

        return {
            "unrealized_profit": unrealized,
            "annual_depreciation_adjustment": annual_adj,
        }

    def build_asset_profit_elimination_journal(
        self,
        unrealized_profit: Decimal,
    ) -> dict[str, Any]:
        """고정자산 미실현이익 소거 분개 (매각 시점).

        분개:
            차변: 유형자산처분이익(매도법인 PL) unrealized_profit
            대변: 유형자산(매수법인 BS)         unrealized_profit
        """
        return {
            "debit": {
                "account": "유형자산처분이익",
                "entity_role": "seller",
                "amount": unrealized_profit,
            },
            "credit": {
                "account": "유형자산",
                "entity_role": "buyer",
                "amount": unrealized_profit,
            },
            "journal_type": "asset_unrealized_profit",
        }

    def eliminate_intercompany_loan(
        self,
        principal: Decimal,
        interest_period: Decimal,
        interest_accrued: Decimal,
    ) -> dict[str, Any]:
        """BR-CSL-018: 내부대여금/차입금 및 이자 소거.

        구성 요소:
            1) 원금 상계: 대여금 vs 차입금
            2) 기간 이자 소거: 이자수익 vs 이자비용 (PL)
            3) 미수/미지급 이자 소거 (BS)

        Args:
            principal: 원금 잔액
            interest_period: 당기 기간 이자 (PL 항목)
            interest_accrued: 미수/미지급 이자 (BS 항목)

        Returns:
            principal/interest/accrued 소거 금액 및 합계
        """
        total = principal + interest_period + interest_accrued
        return {
            "principal_eliminated": principal,
            "interest_eliminated": interest_period,
            "accrued_interest_eliminated": interest_accrued,
            "total_eliminated": total,
        }

    def build_loan_elimination_journals(
        self,
        principal: Decimal,
        interest_period: Decimal,
        interest_accrued: Decimal,
    ) -> list[dict[str, Any]]:
        """BR-CSL-018: 대여금/이자/미수이자 소거 분개 3종 생성."""
        journals: list[dict[str, Any]] = []

        if principal > Decimal(0):
            journals.append(
                {
                    "debit": {"account": "내부차입금", "entity_role": "borrower"},
                    "credit": {"account": "내부대여금", "entity_role": "lender"},
                    "amount": principal,
                    "journal_type": "loan_principal",
                }
            )

        if interest_period > Decimal(0):
            journals.append(
                {
                    "debit": {"account": "내부이자수익", "entity_role": "lender"},
                    "credit": {"account": "내부이자비용", "entity_role": "borrower"},
                    "amount": interest_period,
                    "journal_type": "loan_interest",
                }
            )

        if interest_accrued > Decimal(0):
            journals.append(
                {
                    "debit": {"account": "내부미지급이자", "entity_role": "borrower"},
                    "credit": {"account": "내부미수이자", "entity_role": "lender"},
                    "amount": interest_accrued,
                    "journal_type": "loan_accrued",
                }
            )

        return journals

    def eliminate_intercompany_dividend(
        self,
        total_dividend: Decimal,
        ownership_percentage: Decimal,
    ) -> dict[str, Any]:
        """BR-CSL-015: 내부배당 소거 + NCI 배당 배분.

        공식:
            지배기업 수취 배당 = 종속기업 배당총액 x 지분율 / 100
            NCI 배당          = 종속기업 배당총액 x (1 - 지분율 / 100)
            소거 금액          = 지배기업 수취 배당

        Args:
            total_dividend: 종속기업 배당 총액
            ownership_percentage: 지배기업 지분율 (%)

        Returns:
            parent_received, nci_dividend, elimination_amount 딕셔너리
        """
        parent_received = total_dividend * ownership_percentage / _HUNDRED
        nci_dividend = total_dividend - parent_received

        return {
            "parent_received": parent_received,
            "nci_dividend": nci_dividend,
            "elimination_amount": parent_received,
        }

    def build_dividend_elimination_journal(
        self,
        parent_received: Decimal,
    ) -> dict[str, Any]:
        """내부배당 소거 분개.

        분개:
            차변: 배당수익(지배기업 PL)   parent_received
            대변: 이익잉여금(종속기업 BS) parent_received
        """
        return {
            "debit": {
                "account": "배당수익",
                "entity_role": "parent",
                "amount": parent_received,
            },
            "credit": {
                "account": "이익잉여금",
                "entity_role": "subsidiary",
                "amount": parent_received,
            },
            "journal_type": "dividend",
        }
