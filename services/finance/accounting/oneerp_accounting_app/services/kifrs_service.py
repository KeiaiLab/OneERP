"""K-IFRS 매핑 및 재무제표 변환 서비스."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime

from oneerp_core.document import DocStatus
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class KIFRSService:
    """K-IFRS 매핑 및 재무제표 변환 서비스.

    로컬 계정과목을 K-IFRS 계정으로 변환하고,
    기간별 재무제표(재무상태표/손익계산서)를 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._mapping_repo = Repository("kifrs_mappings", tenant_id)
        self._account_repo = Repository("accounts", tenant_id)
        self._journal_repo = Repository("journal_entries", tenant_id)

    def map_account(self, local_account: str) -> str | None:
        """로컬 계정을 K-IFRS 계정으로 변환한다.

        매핑 테이블에서 local_account로 조회하여 k_ifrs_account를 반환.
        매핑이 없으면 None을 반환한다.
        """
        results = self._mapping_repo.find_many(
            {"local_account": local_account, "is_active": True},
            limit=1,
        )
        if not results:
            return None
        return results[0].get("k_ifrs_account")

    def validate_mapping_completeness(self) -> dict:
        """매핑 누락 검증.

        모든 활성 계정과목(is_group=False)에 대해 K-IFRS 매핑이 존재하는지 확인한다.

        Returns:
            {"total_accounts": int, "mapped": int, "unmapped": list[str], "coverage_pct": float}
        """
        # 그룹이 아닌 활성 계정과목만 조회
        accounts = self._account_repo.find_many(
            {"is_group": False},
            limit=10000,
        )
        total = len(accounts)

        if total == 0:
            return {
                "total_accounts": 0,
                "mapped": 0,
                "unmapped": [],
                "coverage_pct": 100.0,
            }

        unmapped: list[str] = []
        mapped = 0

        for account in accounts:
            account_name = account.get("account_name", "")
            kifrs = self.map_account(account_name)
            if kifrs is not None:
                mapped += 1
            else:
                unmapped.append(account_name)

        coverage_pct = round((mapped / total) * 100, 2) if total > 0 else 0.0

        logger.info(
            "K-IFRS 매핑 검증: 전체 %d건, 매핑 %d건, 누락 %d건 (%.1f%%)",
            total,
            mapped,
            len(unmapped),
            coverage_pct,
        )

        return {
            "total_accounts": total,
            "mapped": mapped,
            "unmapped": unmapped,
            "coverage_pct": coverage_pct,
        }

    def generate_financial_statement(
        self,
        period_start: date,
        period_end: date,
        statement_type: str = "balance_sheet",
    ) -> dict:
        """K-IFRS 기준 재무제표를 생성한다.

        Args:
            period_start: 기간 시작일
            period_end: 기간 종료일
            statement_type: "balance_sheet"(재무상태표) 또는 "income_statement"(손익계산서)

        Returns:
            재무제표 딕셔너리
        """
        # 1. 기간 내 제출된 분개전표 조회
        start_dt = datetime(period_start.year, period_start.month, period_start.day, tzinfo=UTC)
        end_dt = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, tzinfo=UTC)

        query = {
            "posting_date": {"$gte": start_dt, "$lte": end_dt},
            "docstatus": DocStatus.SUBMITTED,
        }
        journals = self._journal_repo.find_many(query, limit=10000)

        logger.info(
            "재무제표 생성(%s): %s ~ %s 기간 전표 %d건",
            statement_type,
            period_start,
            period_end,
            len(journals),
        )

        # 2. 계정별 집계 (K-IFRS 변환 포함)
        aggregated = self._aggregate_by_account(journals)

        # 3. 계정 유형별 분류
        account_types = self._get_account_type_map()

        if statement_type == "income_statement":
            return self._build_income_statement(
                aggregated,
                account_types,
                period_start,
                period_end,
            )
        return self._build_balance_sheet(
            aggregated,
            account_types,
            period_start,
            period_end,
        )

    def _aggregate_by_account(self, entries: list[dict]) -> dict[str, float]:
        """분개전표를 K-IFRS 계정별로 집계한다.

        각 항목의 로컬 계정을 K-IFRS로 변환 후
        debit - credit 순액을 계정별로 합산한다.

        Returns:
            {kifrs_account: net_amount(debit-credit)} 딕셔너리
        """
        result: dict[str, float] = {}

        for entry in entries:
            items = entry.get("items", [])
            for item in items:
                local_account = item.get("account", "")
                # K-IFRS 매핑 시도, 없으면 원본 계정 사용
                kifrs_account = self.map_account(local_account) or local_account
                debit = item.get("debit", 0.0)
                credit = item.get("credit", 0.0)
                net = debit - credit
                result[kifrs_account] = result.get(kifrs_account, 0.0) + net

        return result

    def _get_account_type_map(self) -> dict[str, str]:
        """계정과목명 → 계정유형 매핑을 반환한다."""
        accounts = self._account_repo.find_many({}, limit=10000)
        type_map: dict[str, str] = {}

        for acc in accounts:
            name = acc.get("account_name", "")
            acc_type = acc.get("account_type", "")
            type_map[name] = acc_type

            # K-IFRS 매핑된 계정도 같은 유형으로 등록
            kifrs = self.map_account(name)
            if kifrs and kifrs not in type_map:
                type_map[kifrs] = acc_type

        return type_map

    def _build_balance_sheet(
        self,
        aggregated: dict[str, float],
        account_types: dict[str, str],
        period_start: date,
        period_end: date,
    ) -> dict:
        """재무상태표(자산 = 부채 + 자본)를 구성한다."""
        assets: list[dict] = []
        liabilities: list[dict] = []
        equity: list[dict] = []

        for account, net in aggregated.items():
            acc_type = account_types.get(account, "")
            if acc_type == "asset":
                # 자산: debit - credit (net 그대로)
                assets.append({"account": account, "amount": round(net, 2)})
            elif acc_type == "liability":
                # 부채: credit - debit (net 부호 반전)
                liabilities.append({"account": account, "amount": round(-net, 2)})
            elif acc_type == "equity":
                # 자본: credit - debit (net 부호 반전)
                equity.append({"account": account, "amount": round(-net, 2)})

        asset_total = round(sum(item["amount"] for item in assets), 2)
        liability_total = round(sum(item["amount"] for item in liabilities), 2)
        equity_total = round(sum(item["amount"] for item in equity), 2)

        is_balanced = abs(asset_total - (liability_total + equity_total)) < 1e-9

        return {
            "statement_type": "balance_sheet",
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "sections": {
                "assets": {"total": asset_total, "items": assets},
                "liabilities": {"total": liability_total, "items": liabilities},
                "equity": {"total": equity_total, "items": equity},
            },
            "is_balanced": is_balanced,
        }

    def _build_income_statement(
        self,
        aggregated: dict[str, float],
        account_types: dict[str, str],
        period_start: date,
        period_end: date,
    ) -> dict:
        """손익계산서(수익 - 비용 = 당기순이익)를 구성한다."""
        income_items: list[dict] = []
        expense_items: list[dict] = []

        for account, net in aggregated.items():
            acc_type = account_types.get(account, "")
            if acc_type == "income":
                # 수익: credit - debit (net 부호 반전)
                income_items.append({"account": account, "amount": round(-net, 2)})
            elif acc_type == "expense":
                # 비용: debit - credit (net 그대로)
                expense_items.append({"account": account, "amount": round(net, 2)})

        income_total = round(sum(item["amount"] for item in income_items), 2)
        expense_total = round(sum(item["amount"] for item in expense_items), 2)
        net_income = round(income_total - expense_total, 2)

        return {
            "statement_type": "income_statement",
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "sections": {
                "income": {"total": income_total, "items": income_items},
                "expenses": {"total": expense_total, "items": expense_items},
            },
            "net_income": net_income,
        }
