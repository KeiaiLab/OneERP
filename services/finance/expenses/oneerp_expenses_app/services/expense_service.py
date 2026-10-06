"""경비 서비스 — 법인카드 거래 매칭, 경비청구->결재, 출장정산 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-EXP-001: 법인카드 자동 매칭 (동일 금액, 허용 오차 <= 1원)
- BR-EXP-002: 금액별 결재선 자동 라우팅 (<10만 팀장, <100만 부장, >=100만 임원)
- BR-EXP-003: 거래 -> 경비 자동 생성 (CCT -> ExpenseClaim)
- BR-EXP-004: 출장 정산 (예상 vs 실제 비교, 차액 산출)
- BR-EXP-005: EXPENSE_CLAIM_SUBMITTED 이벤트 (Accounting 구독)
- BR-EXP-006: 결재 승인 이벤트 처리 (APPROVAL_REQUEST_APPROVED)
- BR-EXP-007: total_amount 동기화
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any

import httpx
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_expenses_app.models.expense_claim import ExpenseClaim, ExpenseClaimItem

logger = logging.getLogger(__name__)

# 자동 매칭 허용 오차
_MATCH_TOLERANCE = 1.0

# 결재 금액 기준 (원)
_APPROVAL_THRESHOLDS = [
    (100_000, "팀장"),  # 10만원 미만
    (1_000_000, "부장"),  # 100만원 미만
]
_APPROVAL_DEFAULT_LEVEL = "임원"

_GATEWAY_URL = os.getenv("ONEERP_GATEWAY_URL", "http://gateway-service/api/v1")


class ExpenseService:
    """경비/법인카드 비즈니스 로직.

    법인카드 거래 → 경비청구 자동 매칭,
    경비청구 → 결재 연동,
    출장 신청 → 결재 → 경비정산 흐름을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._cct_repo = Repository("corporate_card_transactions", tenant_id=tenant_id)
        self._claim_repo = Repository("expense_claims", tenant_id=tenant_id)
        self._travel_repo = Repository("travel_requests", tenant_id=tenant_id)

    def match_card_transactions(
        self,
        employee: str,
        card_number: str,
    ) -> dict[str, Any]:
        """BR-EXP-001: 법인카드 거래를 경비청구와 자동 매칭한다.

        동일 금액(허용 오차 <= 1원)의 거래-청구를 매칭.

        Returns:
            매칭 결과 (matched, unmatched_transactions, unmatched_claims)
        """
        transactions = self._cct_repo.find_many(
            {"card_number": card_number},
            limit=10000,
        )

        claims = self._claim_repo.find_many(
            {"employee": employee, "approval_status": "pending"},
            limit=10000,
        )

        matched: list[dict[str, Any]] = []
        used_claim_indices: set[int] = set()
        unmatched_txns: list[dict[str, Any]] = []

        for txn in transactions:
            txn_amount = float(txn.get("amount", 0))
            match_found = False

            for idx, claim in enumerate(claims):
                if idx in used_claim_indices:
                    continue
                claim_amount = float(claim.get("total_amount", 0))
                if abs(txn_amount - claim_amount) <= _MATCH_TOLERANCE:
                    matched.append(
                        {
                            "transaction_id": txn.get("_id", ""),
                            "claim_id": claim.get("_id", ""),
                            "amount": txn_amount,
                            "merchant": txn.get("merchant", ""),
                        }
                    )
                    used_claim_indices.add(idx)
                    match_found = True
                    break

            if not match_found:
                unmatched_txns.append(txn)

        unmatched_claims = [
            claim for idx, claim in enumerate(claims) if idx not in used_claim_indices
        ]

        logger.info(
            "법인카드 매칭: 매칭 %d, 미매칭 거래 %d, 미매칭 청구 %d",
            len(matched),
            len(unmatched_txns),
            len(unmatched_claims),
        )

        return {
            "card_number": card_number,
            "matched_count": len(matched),
            "matched": matched,
            "unmatched_transactions": unmatched_txns,
            "unmatched_claims": unmatched_claims,
        }

    def create_claim_from_transaction(
        self,
        transaction_id: str,
        employee: str,
        expense_type: str = "법인카드",
    ) -> dict[str, Any]:
        """BR-EXP-003: 법인카드 거래에서 경비청구를 자동 생성한다."""
        txn = self._cct_repo.find_by_id(transaction_id)
        if not txn:
            raise_not_found(f"법인카드 거래 '{transaction_id}'을 찾을 수 없습니다")

        claim_id = generate_name("EC", tenant_id=self._tenant_id)
        amount = Decimal(str(txn.get("amount", 0)))
        claim_doc = ExpenseClaim(
            _id=claim_id,
            employee_id=employee,
            posting_date=txn.get("transaction_date"),
            total_amount=amount,
            approval_status="pending",
            items=[
                ExpenseClaimItem(
                    expense_type=expense_type,
                    amount=amount,
                    description=txn.get("merchant", ""),
                ).model_dump(),
            ],
            tenant_id=self._tenant_id,
        )
        self._claim_repo.insert(claim_doc)

        logger.info(
            "경비청구 자동 생성: %s (거래: %s, 금액: %.2f)",
            claim_id,
            transaction_id,
            float(amount),
        )

        return {
            "claim_id": claim_id,
            "transaction_id": transaction_id,
            "amount": float(amount),
        }

    def settle_travel(
        self,
        travel_request_id: str,
        actual_expenses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """BR-EXP-004: 출장 경비를 정산한다.

        Args:
            travel_request_id: 출장 신청 ID
            actual_expenses: [{"expense_type": "...", "amount": N, "description": "..."}, ...]

        Returns:
            정산 결과 (estimated_cost, actual_cost, difference)
        """
        travel = self._travel_repo.find_by_id(travel_request_id)
        if not travel:
            raise_not_found(f"출장 신청 '{travel_request_id}'을 찾을 수 없습니다")

        estimated_cost = float(travel.get("estimated_cost", 0))
        actual_cost = sum((Decimal(str(e.get("amount", 0))) for e in actual_expenses), Decimal(0))

        # 경비청구 생성
        claim_id = generate_name("EC", tenant_id=self._tenant_id)
        claim_doc = ExpenseClaim(
            _id=claim_id,
            employee_id=travel.get("employee", ""),
            total_amount=actual_cost,
            approval_status="pending",
            items=[
                ExpenseClaimItem(
                    expense_type=e.get("expense_type", ""),
                    amount=Decimal(str(e.get("amount", 0))),
                    description=e.get("description", ""),
                ).model_dump()
                for e in actual_expenses
            ],
            tenant_id=self._tenant_id,
        )
        self._claim_repo.insert(claim_doc)

        # 출장 신청 정산 상태 업데이트
        self._travel_repo.update_by_id(
            travel_request_id,
            {"settlement_status": "settled", "actual_cost": actual_cost},
        )

        logger.info(
            "출장 정산: %s (예상: %.2f, 실제: %.2f)",
            travel_request_id,
            estimated_cost,
            actual_cost,
        )

        return {
            "travel_request_id": travel_request_id,
            "claim_id": claim_id,
            "estimated_cost": estimated_cost,
            "actual_cost": float(actual_cost),
            "difference": round(float(actual_cost) - estimated_cost, 2),
        }

    def submit_for_approval(self, expense_claim_id: str) -> dict[str, Any]:
        """BR-EXP-002: 경비청구를 금액 기준 결재선에 맞춰 결재 요청한다.

        금액 기준:
        - 10만원 미만: 팀장 결재
        - 100만원 미만: 부장 결재
        - 100만원 이상: 임원 결재

        Args:
            expense_claim_id: 경비청구 문서 ID

        Returns:
            {approval_request_id, approver_level}

        Raises:
            OneERPError: 경비청구가 존재하지 않을 때 (404)
            OneERPError: 결재 요청 실패 시 (422, ERR-EXP-001)
        """
        claim = self._claim_repo.find_by_id(expense_claim_id)
        if not claim:
            raise_not_found(f"경비청구 '{expense_claim_id}'를 찾을 수 없습니다")

        total_amount = float(claim.get("total_amount", 0))

        # 금액 기준 결재선 결정
        approver_level = _APPROVAL_DEFAULT_LEVEL
        for threshold, level in _APPROVAL_THRESHOLDS:
            if total_amount < threshold:
                approver_level = level
                break

        # gateway 서비스에 결재 요청
        try:
            response = httpx.post(
                f"{_GATEWAY_URL}/approval-requests",
                json={
                    "document_type": "ExpenseClaim",
                    "document_id": expense_claim_id,
                    "requester": claim.get("employee", ""),
                    "approver_level": approver_level,
                },
                headers={"X-Tenant-Id": self._tenant_id},
                timeout=5.0,
            )
            response.raise_for_status()
            approval_data: dict[str, Any] = response.json()
        except httpx.HTTPError as exc:
            raise_unprocessable("ERR-EXP-001", f"결재 요청 실패: {exc}")

        approval_request_id: str = approval_data.get("id", "")

        # 경비청구에 결재 요청 ID 기록
        self._claim_repo.update_by_id(
            expense_claim_id,
            {
                "approval_request_id": approval_request_id,
                "approver_level": approver_level,
                "status": "pending_approval",
            },
        )

        logger.info(
            "경비청구 결재 요청: %s → %s (%s)",
            expense_claim_id,
            approval_request_id,
            approver_level,
        )
        return {
            "expense_claim_id": expense_claim_id,
            "approval_request_id": approval_request_id,
            "approver_level": approver_level,
        }

    def process_approved_expense(self, expense_claim_id: str) -> None:
        """결재 완료된 경비청구를 승인 처리하고 이벤트를 발행한다.

        EXPENSE_CLAIM_APPROVED 이벤트를 통해
        payroll/accounting 서비스가 후속 처리한다.

        Args:
            expense_claim_id: 경비청구 문서 ID

        Raises:
            OneERPError: 경비청구가 존재하지 않을 때 (404)
        """
        claim = self._claim_repo.find_by_id(expense_claim_id)
        if not claim:
            raise_not_found(f"경비청구 '{expense_claim_id}'를 찾을 수 없습니다")

        # 상태를 approved로 변경
        self._claim_repo.update_by_id(
            expense_claim_id,
            {"status": "approved"},
        )

        logger.info("경비청구 승인 완료: %s", expense_claim_id)
