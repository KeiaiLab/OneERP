"""수금/지급 대사 서비스 — 미수금/미지급금 자동 대사 비즈니스 로직."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.payment_reconciliation import PaymentReconciliation

logger = logging.getLogger(__name__)

# 대사 허용 오차
_TOLERANCE = 0.01


class PaymentReconciliationService:
    """수금/지급 대사 비즈니스 로직.

    미수금(매출채권)과 입금, 미지급금(매입채무)과 출금을 자동 매칭한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._prec_repo = Repository("payment_reconciliations", tenant_id=tenant_id)
        self._ar_repo = Repository("accounts_receivable", tenant_id=tenant_id)
        self._ap_repo = Repository("accounts_payable", tenant_id=tenant_id)
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)

    def reconcile_receivables(
        self,
        party: str,
        from_date: Any,
        to_date: Any,
    ) -> dict[str, Any]:
        """매출채권(미수금)을 자동 대사한다.

        해당 고객의 미수금과 입금 전표를 금액 기반으로 매칭.

        Args:
            party: 고객 ID
            from_date: 대사 기간 시작일
            to_date: 대사 기간 종료일

        Returns:
            대사 결과 (prec_id, matched, unmatched_invoices, unmatched_payments)
        """
        # 미수금 조회
        receivables = self._ar_repo.find_many(
            {"customer": party},
            limit=10000,
        )

        # 입금 전표 조회 (해당 고객 관련, 제출 상태)
        payments = self._je_repo.find_many(
            {
                "posting_date": {"$gte": from_date, "$lte": to_date},
                "docstatus": 1,
                "party": party,
                "voucher_type": "payment_entry",
            },
            limit=10000,
        )

        # 자동 매칭
        matched, unmatched_inv, unmatched_pay = self._auto_match_amounts(
            invoices=receivables,
            payments=payments,
            invoice_amount_field="outstanding_amount",
            payment_amount_field="total_credit",
        )

        # 대사 문서 생성
        prec_id = generate_name("PREC", tenant_id=self._tenant_id)
        doc = PaymentReconciliation(
            _id=prec_id,
            party_type="Customer",
            party=party,
            receivable_payable_account="",
            from_date=from_date,
            to_date=to_date,
            tenant_id=self._tenant_id,
        )
        self._prec_repo.insert(doc)

        total_reconciled = sum(m["amount"] for m in matched)

        logger.info(
            "매출채권 대사: %s (고객: %s, 매칭: %d건, 금액: %.2f)",
            prec_id,
            party,
            len(matched),
            total_reconciled,
        )

        return {
            "prec_id": prec_id,
            "party_type": "Customer",
            "party": party,
            "matched_count": len(matched),
            "matched": matched,
            "total_reconciled": total_reconciled,
            "unmatched_invoices": unmatched_inv,
            "unmatched_payments": unmatched_pay,
        }

    def reconcile_payables(
        self,
        party: str,
        from_date: Any,
        to_date: Any,
    ) -> dict[str, Any]:
        """매입채무(미지급금)을 자동 대사한다.

        해당 공급사의 미지급금과 출금 전표를 금액 기반으로 매칭.

        Args:
            party: 공급사 ID
            from_date: 대사 기간 시작일
            to_date: 대사 기간 종료일

        Returns:
            대사 결과
        """
        payables = self._ap_repo.find_many(
            {"supplier": party},
            limit=10000,
        )

        payments = self._je_repo.find_many(
            {
                "posting_date": {"$gte": from_date, "$lte": to_date},
                "docstatus": 1,
                "party": party,
                "voucher_type": "payment_entry",
            },
            limit=10000,
        )

        matched, unmatched_inv, unmatched_pay = self._auto_match_amounts(
            invoices=payables,
            payments=payments,
            invoice_amount_field="outstanding_amount",
            payment_amount_field="total_debit",
        )

        prec_id = generate_name("PREC", tenant_id=self._tenant_id)
        doc = PaymentReconciliation(
            _id=prec_id,
            party_type="Supplier",
            party=party,
            receivable_payable_account="",
            from_date=from_date,
            to_date=to_date,
            tenant_id=self._tenant_id,
        )
        self._prec_repo.insert(doc)

        total_reconciled = sum(m["amount"] for m in matched)

        logger.info(
            "매입채무 대사: %s (공급사: %s, 매칭: %d건, 금액: %.2f)",
            prec_id,
            party,
            len(matched),
            total_reconciled,
        )

        return {
            "prec_id": prec_id,
            "party_type": "Supplier",
            "party": party,
            "matched_count": len(matched),
            "matched": matched,
            "total_reconciled": total_reconciled,
            "unmatched_invoices": unmatched_inv,
            "unmatched_payments": unmatched_pay,
        }

    def get_unreconciled_invoices(
        self,
        party_type: str,
        party: str,
    ) -> list[dict[str, Any]]:
        """미대사 송장 목록을 조회한다."""
        if party_type == "Customer":
            docs = self._ar_repo.find_many({"customer": party}, limit=10000)
        else:
            docs = self._ap_repo.find_many({"supplier": party}, limit=10000)

        return [doc for doc in docs if float(doc.get("outstanding_amount", 0)) > _TOLERANCE]

    # -- 내부 헬퍼 --

    def _auto_match_amounts(
        self,
        invoices: list[dict[str, Any]],
        payments: list[dict[str, Any]],
        invoice_amount_field: str,
        payment_amount_field: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """금액 기반 자동 매칭.

        Returns:
            (matched, unmatched_invoices, unmatched_payments)
        """
        matched: list[dict[str, Any]] = []
        used_payment_indices: set[int] = set()

        unmatched_invoices: list[dict[str, Any]] = []

        for inv in invoices:
            inv_amount = float(inv.get(invoice_amount_field, 0))
            if inv_amount < _TOLERANCE:
                continue

            match_found = False
            for idx, pay in enumerate(payments):
                if idx in used_payment_indices:
                    continue
                pay_amount = float(pay.get(payment_amount_field, 0))
                if abs(inv_amount - pay_amount) < _TOLERANCE:
                    matched.append(
                        {
                            "invoice_id": inv.get("_id", inv.get("invoice_id", "")),
                            "payment_id": pay.get("_id", ""),
                            "amount": inv_amount,
                        }
                    )
                    used_payment_indices.add(idx)
                    match_found = True
                    break

            if not match_found:
                unmatched_invoices.append(inv)

        unmatched_payments = [
            pay for idx, pay in enumerate(payments) if idx not in used_payment_indices
        ]

        return matched, unmatched_invoices, unmatched_payments
