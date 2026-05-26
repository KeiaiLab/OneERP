"""지분법 서비스 — 관계기업/공동기업 투자 지분법 회계 처리.

L2 비즈니스 룰 매핑:
- BR-CSL-014: 지분법 손익 인식
- BR-CSL-016: 유효 지분율 계산 (직접 + 간접)

참조 회계 기준:
- K-IFRS 제1028호 "관계기업과 공동기업에 대한 투자"
  * 단락 10: 지분법 적용 의무
  * 단락 11: 투자자산 장부가액 = 취득원가 + 투자자 지분 변동
  * 단락 38: 투자자 지분이 영(0) 이하가 되면 추가 손실 인식 중단
  * 단락 40~43: 손상 검사 (장부가 vs 회수가능액)

분개 (지분법 손익 인식):
    차변: 관계기업투자(BS)     지분법 손익
    대변: 지분법이익(PL)       지분법 손익
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

_HUNDRED = Decimal(100)


class EquityMethodService:
    """지분법 회계 처리 비즈니스 로직.

    K-IFRS 1028 기반의 순수 계산 서비스. Repository 의존성이 없어
    단위 테스트가 수월하며, 상위 오케스트레이터(배치/라우트)에서
    투자자산/관계기업 컨텍스트를 주입받아 사용한다.
    """

    def calculate_equity_income(
        self,
        investee_net_income: Decimal,
        ownership_percentage: Decimal,
    ) -> Decimal:
        """BR-CSL-014: 지분법 손익 = 피투자자 당기순이익 x 지분율.

        Args:
            investee_net_income: 관계기업/공동기업 당기순이익(손실은 음수)
            ownership_percentage: 투자자 지분율(%, 0~100)

        Returns:
            투자자 귀속 지분법 손익
        """
        return investee_net_income * ownership_percentage / _HUNDRED

    def calculate_equity_oci(
        self,
        investee_oci: Decimal,
        ownership_percentage: Decimal,
    ) -> Decimal:
        """관계기업 기타포괄손익(OCI)에 지분율을 적용한 귀속액을 산출한다."""
        return investee_oci * ownership_percentage / _HUNDRED

    def calculate_investment_book_value(
        self,
        acquisition_cost: Decimal,
        cumulative_equity_income: Decimal,
        cumulative_equity_oci: Decimal,
        cumulative_dividends_received: Decimal,
        *,
        floor_at_zero: bool = False,
    ) -> Decimal:
        """BR-CSL-014: 지분법 투자자산 장부가액 산출.

        공식:
            장부가액 = 취득원가
                    + 누적 지분법 손익
                    + 누적 지분법 OCI
                    - 누적 수령 배당금

        K-IFRS 1028.38에 따라 추가 손실 인식을 중단해야 하는 경우(투자자
        지분이 영(0) 이하)를 위해 ``floor_at_zero=True`` 옵션을 제공한다.

        Args:
            acquisition_cost: 취득원가
            cumulative_equity_income: 누적 지분법 손익
            cumulative_equity_oci: 누적 지분법 OCI
            cumulative_dividends_received: 누적 수령 배당금
            floor_at_zero: True이면 음수가 되는 경우 0으로 제한

        Returns:
            산출된 투자자산 장부가액
        """
        book_value = (
            acquisition_cost
            + cumulative_equity_income
            + cumulative_equity_oci
            - cumulative_dividends_received
        )

        if floor_at_zero and book_value < Decimal(0):
            logger.debug(
                "지분법 투자 장부가액이 0 이하 — K-IFRS 1028.38에 따라 0으로 제한",
            )
            return Decimal(0)

        return book_value

    def calculate_effective_ownership(
        self,
        relations: list[dict[str, Any]],
        parent_entity: str,
        target_entity: str,
        *,
        max_depth: int = 10,
    ) -> Decimal:
        """BR-CSL-016: 유효 지분율 계산 (직접 + 간접).

        공식:
            유효_지분율(P->S) = 직접_지분율(P->S)
                             + sum(유효_지분율(P->M_i) * 직접_지분율(M_i->S) / 100)

        깊이 우선 탐색으로 모든 경로를 합산한다. 순환 지분(상호출자)은
        방문 집합으로 차단하여 무한 루프를 방지한다.

        Args:
            relations: 지분 관계 목록. 각 항목은 ``investor`` / ``investee``
                       / ``ownership`` 키를 가진다. ``ownership``은 %.
            parent_entity: 최상위 투자자 식별자
            target_entity: 대상 피투자자 식별자
            max_depth: 탐색 최대 깊이(순환 방지용)

        Returns:
            유효 지분율(%). 경로가 없으면 0.
        """
        # 동일 법인 비교 시 100%
        if parent_entity == target_entity:
            return _HUNDRED

        def _walk(current: str, path_product: Decimal, visited: set[str], depth: int) -> Decimal:
            """현재 법인에서 target까지의 모든 경로 지분율 합."""
            if depth > max_depth:
                return Decimal(0)

            total = Decimal(0)
            for rel in relations:
                if rel.get("investor") != current:
                    continue
                investee = rel.get("investee")
                if investee is None or investee in visited:
                    continue
                direct_pct = Decimal(str(rel.get("ownership", 0)))
                # 현재까지 곱해진 경로 지분율에 이번 direct 지분율을 곱함
                segment = path_product * direct_pct / _HUNDRED

                if investee == target_entity:
                    total += segment
                    continue

                # 중간 노드 재귀
                total += _walk(
                    current=investee,
                    path_product=segment,
                    visited=visited | {investee},
                    depth=depth + 1,
                )
            return total

        return _walk(
            current=parent_entity,
            path_product=_HUNDRED,
            visited={parent_entity},
            depth=0,
        )

    def test_impairment(
        self,
        book_value: Decimal,
        recoverable_amount: Decimal,
    ) -> dict[str, Any]:
        """K-IFRS 1028.40~43: 지분법 투자자산 손상 검사.

        장부가액 > 회수가능액 이면 손상차손을 인식한다.

        Args:
            book_value: 투자자산 장부가액
            recoverable_amount: 회수가능액(사용가치와 순공정가치 중 큰 값)

        Returns:
            impaired(bool), impairment_loss(Decimal), new_book_value(Decimal)
        """
        if book_value > recoverable_amount:
            loss = book_value - recoverable_amount
            return {
                "impaired": True,
                "impairment_loss": loss,
                "new_book_value": recoverable_amount,
            }

        return {
            "impaired": False,
            "impairment_loss": Decimal(0),
            "new_book_value": book_value,
        }

    def build_equity_method_journal(
        self,
        equity_income: Decimal,
        *,
        investment_account: str = "관계기업투자",
        income_account: str = "지분법이익",
    ) -> dict[str, Any]:
        """지분법 손익 인식 분개를 생성한다.

        양(+)이면 이익, 음(-)이면 손실 분개를 생성한다.
        """
        if equity_income >= Decimal(0):
            debit = {"account": investment_account, "amount": equity_income}
            credit = {"account": income_account, "amount": equity_income}
        else:
            amount = abs(equity_income)
            debit = {"account": "지분법손실", "amount": amount}
            credit = {"account": investment_account, "amount": amount}

        return {
            "debit": debit,
            "credit": credit,
            "journal_type": "equity_method",
            "is_balanced": True,
        }
