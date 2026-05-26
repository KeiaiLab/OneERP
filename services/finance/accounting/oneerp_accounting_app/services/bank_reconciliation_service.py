"""은행 대사 서비스 — 은행 거래와 내부 전표 자동 매칭 비즈니스 로직."""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.bank_reconciliation import BankReconciliation

logger = logging.getLogger(__name__)

# BR-ACCT-014: 자동 매칭 허용 오차 — 환경변수로 설정 가능 (기본 0.01원)
_MATCH_TOLERANCE = float(os.getenv("ONEERP_BANK_MATCH_TOLERANCE", "0.01"))


class BankReconciliationService:
    """은행 대사 비즈니스 로직.

    은행 잔액과 시스템 잔액을 비교하고,
    은행 거래와 내부 분개전표를 자동/수동 매칭한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._br_repo = Repository("bank_reconciliations", tenant_id=tenant_id)
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)

    def create_reconciliation(
        self,
        bank_account: str,
        from_date: Any,
        to_date: Any,
        bank_balance: float,
    ) -> dict[str, Any]:
        """은행 대사를 생성한다.

        시스템 잔액을 자동 계산하고 차이를 산출한다.

        Args:
            bank_account: 은행 계정 ID
            from_date: 대사 시작일
            to_date: 대사 종료일
            bank_balance: 은행 명세서상 잔액

        Returns:
            대사 생성 결과 (br_id, system_balance, difference)
        """
        system_balance = self._calculate_system_balance(bank_account, from_date, to_date)
        bank_balance_dec = Decimal(str(bank_balance))
        difference_dec = round(bank_balance_dec - system_balance, 2)
        difference = float(difference_dec)

        br_id = generate_name("BR", tenant_id=self._tenant_id)
        doc = BankReconciliation(
            _id=br_id,
            bank_account=bank_account,
            from_date=from_date,
            to_date=to_date,
            bank_balance=bank_balance_dec,
            system_balance=system_balance,
            difference=difference_dec,
            tenant_id=self._tenant_id,
        )
        self._br_repo.insert(doc)

        logger.info(
            "은행 대사 생성: %s (계정: %s, 차이: %.2f)",
            br_id,
            bank_account,
            difference,
        )

        return {
            "br_id": br_id,
            "bank_balance": bank_balance,
            "system_balance": float(system_balance),
            "difference": difference,
            "is_reconciled": abs(difference) < _MATCH_TOLERANCE,
        }

    def auto_match(
        self,
        br_id: str,
        bank_transactions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """은행 거래와 내부 전표를 자동 매칭한다.

        금액 일치 기준으로 은행 거래를 분개전표와 1:1 매칭.
        매칭 기준: 동일 금액 ± 허용 오차.

        Args:
            br_id: 은행 대사 ID
            bank_transactions: 은행 거래 목록
                [{"reference": "...", "amount": 100.0, "date": "...", "description": "..."}, ...]

        Returns:
            매칭 결과 (matched, unmatched_bank, unmatched_system)
        """
        br_doc = self._br_repo.find_by_id(br_id)
        if not br_doc:
            msg = f"은행 대사 '{br_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        # 기간 내 시스템 전표 조회
        system_entries = self._je_repo.find_many(
            {
                "posting_date": {
                    "$gte": br_doc["from_date"],
                    "$lte": br_doc["to_date"],
                },
                "docstatus": DocStatus.SUBMITTED,
            },
            limit=10000,
        )

        # 전표에서 해당 은행 계정의 순액 추출
        system_items = self._extract_bank_items(system_entries, br_doc["bank_account"])

        # 금액 기반 매칭
        matched: list[dict[str, Any]] = []
        unmatched_bank: list[dict[str, Any]] = []
        used_system_indices: set[int] = set()

        for txn in bank_transactions:
            txn_amount = Decimal(str(txn.get("amount", 0)))
            match_found = False

            for idx, sys_item in enumerate(system_items):
                if idx in used_system_indices:
                    continue
                if abs(txn_amount - sys_item["net_amount"]) < Decimal(str(_MATCH_TOLERANCE)):
                    matched.append(
                        {
                            "bank_transaction": txn,
                            "system_entry": sys_item,
                        }
                    )
                    used_system_indices.add(idx)
                    match_found = True
                    break

            if not match_found:
                unmatched_bank.append(txn)

        unmatched_system = [
            item for idx, item in enumerate(system_items) if idx not in used_system_indices
        ]

        logger.info(
            "자동 매칭 완료: %s (매칭: %d, 미매칭 은행: %d, 미매칭 시스템: %d)",
            br_id,
            len(matched),
            len(unmatched_bank),
            len(unmatched_system),
        )

        return {
            "br_id": br_id,
            "matched_count": len(matched),
            "matched": matched,
            "unmatched_bank": unmatched_bank,
            "unmatched_system": unmatched_system,
        }

    def get_unreconciled_entries(
        self,
        bank_account: str,
        from_date: Any,
        to_date: Any,
    ) -> list[dict[str, Any]]:
        """미대사 전표 항목을 조회한다."""
        entries = self._je_repo.find_many(
            {
                "posting_date": {"$gte": from_date, "$lte": to_date},
                "docstatus": DocStatus.SUBMITTED,
            },
            limit=10000,
        )
        return self._extract_bank_items(entries, bank_account)

    # -- 내부 헬퍼 --

    def _calculate_system_balance(
        self,
        bank_account: str,
        from_date: Any,
        to_date: Any,
    ) -> Decimal:
        """기간 내 시스템 은행 계정 잔액을 계산한다."""
        entries = self._je_repo.find_many(
            {
                "posting_date": {"$gte": from_date, "$lte": to_date},
                "docstatus": DocStatus.SUBMITTED,
            },
            limit=50000,
        )

        balance = Decimal(0)
        for je in entries:
            for item in je.get("items", []):
                if item.get("account") == bank_account:
                    balance += Decimal(str(item.get("debit", 0))) - Decimal(
                        str(item.get("credit", 0))
                    )

        return balance.quantize(Decimal("0.01"))

    def _extract_bank_items(
        self,
        entries: list[dict[str, Any]],
        bank_account: str,
    ) -> list[dict[str, Any]]:
        """분개전표에서 은행 계정 관련 항목을 추출한다."""
        items: list[dict[str, Any]] = []
        for je in entries:
            for item in je.get("items", []):
                if item.get("account") == bank_account:
                    debit = Decimal(str(item.get("debit", 0)))
                    credit = Decimal(str(item.get("credit", 0)))
                    items.append(
                        {
                            "journal_entry_id": je["_id"],
                            "posting_date": je.get("posting_date"),
                            "debit": debit,
                            "credit": credit,
                            "net_amount": debit - credit,
                            "remark": item.get("remark", je.get("remark", "")),
                        }
                    )
        return items
