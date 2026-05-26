"""소거 서비스 — 내부거래 대사, 소�� 전표 생성, 미실현이익 계산.

L2 비즈니스 룰 매핑:
- BR-CSL-002: 소거 전표 차대��� 일치
- BR-CSL-006: 내부거래 양방향 대사
- BR-CSL-007: 미실현이익 소거 (재고)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.repository import Repository

from oneerp_finance_extra_app.consolidation.models.intercompany_balance import MatchStatus

logger = logging.getLogger(__name__)

# 차대변 허용 오차 (1원)
_DEBIT_CREDIT_TOLERANCE = Decimal(1)


def _raise_unprocessable(error_code: str, detail: str) -> None:
    """422 Unprocessable Entity 에러를 발생시킨다."""
    raise OneERPError(status_code=422, error=error_code, detail=detail)


class EliminationService:
    """소거 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._icb_repo = Repository("intercompany_balances", tenant_id=tenant_id)
        self._rule_repo = Repository("elimination_rules", tenant_id=tenant_id)
        self._period_repo = Repository("consolidation_periods", tenant_id=tenant_id)

    def reconcile_intercompany(
        self,
        entity_a_amount: Decimal,
        entity_b_amount: Decimal,
        tolerance_amount: Decimal = Decimal(1),
        tolerance_percentage: Decimal = Decimal("0.1"),
    ) -> dict[str, Any]:
        """BR-CSL-006: 내부거래 양방향 대사.

        매도법인과 매수법인의 금액을 비교하여 매칭 상태를 결정한다.

        Returns:
            match_status, difference_amount, difference_percentage 딕셔너리
        """
        diff_amount = abs(entity_a_amount - entity_b_amount)
        max_amount = max(abs(entity_a_amount), abs(entity_b_amount))

        if max_amount == Decimal(0):
            diff_pct = Decimal(0)
        else:
            diff_pct = diff_amount / max_amount * Decimal(100)

        if diff_amount == Decimal(0):
            status = MatchStatus.MATCHED
        elif diff_amount <= tolerance_amount or diff_pct <= tolerance_percentage:
            status = MatchStatus.WITHIN_TOLERANCE
        else:
            status = MatchStatus.MISMATCH

        return {
            "match_status": status,
            "difference_amount": diff_amount,
            "difference_percentage": diff_pct,
        }

    def validate_debit_credit_balance(
        self,
        debit_total: Decimal,
        credit_total: Decimal,
        tolerance: Decimal = _DEBIT_CREDIT_TOLERANCE,
    ) -> bool:
        """BR-CSL-002: 소거 전표 차대변 일치 검증.

        Returns:
            일치하면 True
        """
        return abs(debit_total - credit_total) <= tolerance

    def calculate_unrealized_profit_inventory(
        self,
        ending_inventory_amount: Decimal,
        internal_margin_rate: Decimal,
    ) -> Decimal:
        """BR-CSL-007: 재고 미실현이익 산출.

        Args:
            ending_inventory_amount: 기말 내부매입 재고 금액
            internal_margin_rate: 내부 마진율 (0~1 범위, 예: 0.25 = 25%)

        Returns:
            미실현이익 금액
        """
        return ending_inventory_amount * internal_margin_rate

    def execute_elimination(self, period_id: str) -> dict[str, Any]:
        """소거 실행 — 기간의 모든 내부거래에 대해 소거 전표를 생성한다.

        Args:
            period_id: 연결 기간 ID

        Returns:
            소거 실행 결과 (elimination_count, total_amount)
        """
        # 미대사 건 존재 여부 확인
        balances = self._icb_repo.find_many(
            {"period_id": period_id},
            limit=10000,
        )

        if not balances:
            _raise_unprocessable(
                "ERR-CSL-071",
                "내부거래 잔액이 수집되지 않았습니다. "
                "먼저 내부거래 수집(/intercompany/collect)을 실행해주세요.",
            )

        # mismatch 건 확인
        mismatch_count = sum(1 for b in balances if b.get("match_status") == MatchStatus.MISMATCH)
        if mismatch_count > 0:
            _raise_unprocessable(
                "ERR-CSL-070",
                f"미해결 내부거래 불일치가 {mismatch_count}건 있습니다. "
                "불일치��� 해결(force-match 또는 수정)한 후 소거를 실행해주세요.",
            )

        # 활성 ��거 규칙 조회 (우선순위 순)
        rules = self._rule_repo.find_many(
            {"status": "active"},
            limit=1000,
        )
        rules.sort(key=lambda r: r.get("priority", 100))

        elimination_count = 0
        total_amount = Decimal(0)

        for balance in balances:
            if balance.get("elimination_entry_id"):
                # 이미 소거된 잔액 건너뛰기
                continue

            matched = balance.get("match_status") in (
                MatchStatus.MATCHED,
                MatchStatus.WITHIN_TOLERANCE,
            )
            if not matched:
                continue

            # 소거 ��액 (보고통화 기준)
            amount = Decimal(
                str(balance.get("entity_a_translated_amount") or balance.get("entity_a_amount", 0))
            )
            elimination_count += 1
            total_amount += abs(amount)

        return {
            "period_id": period_id,
            "elimination_count": elimination_count,
            "total_amount": total_amount,
        }
