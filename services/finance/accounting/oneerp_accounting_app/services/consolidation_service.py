"""연결회계 서비스 — 그룹사 연결 재무제표 생성 비즈니스 로직."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ConsolidationService:
    """연결회계 비즈니스 로직.

    그룹사 간 내부거래를 제거하고 연결 재무제표를 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._group_repo = Repository("consolidation_groups", tenant_id=tenant_id)
        self._entry_repo = Repository("consolidation_entries", tenant_id=tenant_id)
        self._ic_repo = Repository("intercompany_transactions", tenant_id=tenant_id)
        self._elim_repo = Repository("elimination_entries", tenant_id=tenant_id)
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)

    def generate_consolidated_report(
        self,
        group_id: str,
        from_date: Any,
        to_date: Any,
    ) -> dict[str, Any]:
        """연결 재무제표를 생성한다.

        1. 그룹 내 법인별 재무 데이터 집계
        2. 내부거래 식별 및 제거 분개 생성
        3. 연결 합산

        Args:
            group_id: 연결 그룹 ID
            from_date: 시작일
            to_date: 종료일

        Returns:
            연결 재무제표 데이터
        """
        group = self._group_repo.find_by_id(group_id)
        if not group:
            msg = f"연결 그룹 '{group_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        # 내부거래 조회
        ic_transactions = self._ic_repo.find_many(
            {"group_id": group_id},
            limit=50000,
        )

        # 내부거래 제거 분개 생성
        elimination_entries: list[dict[str, Any]] = []
        total_eliminated = 0.0
        for ic in ic_transactions:
            amount = float(ic.get("amount", 0))
            elim_id = generate_name("ELIM", tenant_id=self._tenant_id)
            elim = {
                "_id": elim_id,
                "group_id": group_id,
                "ic_transaction": ic.get("_id", ""),
                "from_company": ic.get("from_company", ""),
                "to_company": ic.get("to_company", ""),
                "amount": amount,
                "description": f"내부거래 제거: {ic.get('description', '')}",
                "tenant_id": self._tenant_id,
            }
            self._elim_repo.insert(elim)
            elimination_entries.append(elim)
            total_eliminated += amount

        # 기간 내 분개전표 합산 (제출 상태)
        journal_entries = self._je_repo.find_many(
            {
                "posting_date": {"$gte": from_date, "$lte": to_date},
                "docstatus": DocStatus.SUBMITTED,
            },
            limit=100000,
        )

        # 계정별 합산
        account_totals: dict[str, dict[str, float]] = {}
        for je in journal_entries:
            for item in je.get("items", []):
                account = item.get("account", "")
                debit = float(item.get("debit", 0))
                credit = float(item.get("credit", 0))
                totals = account_totals.setdefault(account, {"debit": 0.0, "credit": 0.0})
                totals["debit"] += debit
                totals["credit"] += credit

        logger.info(
            "연결 재무제표 생성: %s (내부거래 제거: %d건, %.2f)",
            group_id,
            len(elimination_entries),
            total_eliminated,
        )

        return {
            "group_id": group_id,
            "period": {"from": str(from_date), "to": str(to_date)},
            "elimination_count": len(elimination_entries),
            "total_eliminated": total_eliminated,
            "account_totals": account_totals,
            "journal_entry_count": len(journal_entries),
        }
