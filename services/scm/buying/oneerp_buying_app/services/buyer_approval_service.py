"""구매 승인 매트릭스 서비스 — 금액별 결재자 자동 라우팅 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-BUY-007: 구매 승인 금액 매칭 (min_amount <= 금액 <= max_amount)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class BuyerApprovalService:
    """금액별 구매 결재 자동 라우팅 비즈니스 로직.

    BuyerApprovalMatrix에 설정된 금액 범위에 따라
    적절한 결재자를 자동 결정한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._matrix_repo = Repository("buyer_approval_matrices", tenant_id=tenant_id)

    def get_approver(
        self,
        item_group: str,
        amount: float,
    ) -> dict[str, Any]:
        """금액에 맞는 결재자를 조회한다.

        Args:
            item_group: 아이템 그룹 (예: "원자재", "소모품")
            amount: 구매 금액

        Returns:
            결재자 정보 (approver, matrix_id)

        Raises:
            OneERPError: 매칭되는 승인 매트릭스가 없을 때
        """
        matrices = self._matrix_repo.find_many(
            {"item_group": item_group, "is_active": True},
            limit=100,
        )

        # 금액 범위에 맞는 매트릭스 찾기
        for matrix in matrices:
            min_amount = float(matrix.get("min_amount", 0))
            max_amount = float(matrix.get("max_amount", float("inf")))
            if min_amount <= amount <= max_amount:
                approver = matrix.get("approver", "")
                logger.info(
                    "구매 결재자 결정: %s (그룹: %s, 금액: %.2f, 범위: %.2f~%.2f)",
                    approver,
                    item_group,
                    amount,
                    min_amount,
                    max_amount,
                )
                return {
                    "approver": approver,
                    "matrix_id": matrix.get("_id", ""),
                    "item_group": item_group,
                    "amount": amount,
                    "min_amount": min_amount,
                    "max_amount": max_amount,
                }

        raise OneERPError(
            status_code=422,
            error="ERR-BUY-032",
            detail=f"금액에 해당하는 승인 매트릭스가 없습니다 (그룹: '{item_group}', 금액: {amount})",
        )

    def get_all_approvers_for_amount(
        self,
        amount: float,
    ) -> list[dict[str, Any]]:
        """금액에 해당하는 모든 아이템 그룹의 결재자를 조회한다."""
        matrices = self._matrix_repo.find_many(
            {"is_active": True},
            limit=1000,
        )

        result: list[dict[str, Any]] = []
        for matrix in matrices:
            min_amount = float(matrix.get("min_amount", 0))
            max_amount = float(matrix.get("max_amount", float("inf")))
            if min_amount <= amount <= max_amount:
                result.append(
                    {
                        "approver": matrix.get("approver", ""),
                        "item_group": matrix.get("item_group", ""),
                        "matrix_id": matrix.get("_id", ""),
                    }
                )

        return result
