"""재무비율 분석 서비스 — 유동성·안정성·수익성 5대 비율 자동 산출.

근거 표준 (K-IFRS, 재무분석 일반 원칙):
- 유동비율(Current Ratio): 단기 채무 지급 능력 (200% 이상 권장)
- 부채비율(Debt-to-Equity): 자본 대비 부채 (200% 이하 안정)
- 자기자본비율(Equity Ratio): 총자산 대비 자기자본 (50% 이상 안정)
- ROA(Return on Assets): 자산 활용 효율 (업종 평균 5~10%)
- ROE(Return on Equity): 주주 자본 수익률 (15% 이상 우수)

L2 비즈니스 룰 매핑:
- BR-ACCT-020 (확장): 손익 계산 로직 활용
- 신규 BR-ACCT-FRA-001~005 후보: 5대 비율 산출 표준

설계 메모:
- 모든 분모 0 케이스는 None 반환 (DivisionByZero 방지).
- 유동/비유동 분류는 Account 마스터의 is_current 플래그를 우선 사용.
- 마스터에 is_current가 없으면 계정과목명에 "유동" 키워드 포함 여부로 판정.
- 비율 결과는 소수점 2자리 (퍼센트는 2자리, 배수는 2자리).
- 산업별 벤치마크는 BR-ACCT-FRA-006에서 추후 관리.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.financial_ratio_report import FinancialRatioReport

logger = logging.getLogger(__name__)

# 비율 반올림 단위 (소수점 2자리)
_RATIO_QUANT = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    """다양한 입력을 Decimal로 안전하게 변환한다."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal(0)
    return Decimal(str(value))


def _safe_ratio(
    numerator: Decimal, denominator: Decimal, multiplier: Decimal = Decimal(1)
) -> Decimal | None:
    """0 분모를 안전하게 처리하는 비율 계산."""
    if denominator == 0:
        return None
    result = (numerator / denominator) * multiplier
    return result.quantize(_RATIO_QUANT, rounding=ROUND_HALF_UP)


def calculate_current_ratio(
    current_assets: Decimal,
    current_liabilities: Decimal,
) -> Decimal | None:
    """유동비율 = 유동자산 / 유동부채 (배수)."""
    return _safe_ratio(_to_decimal(current_assets), _to_decimal(current_liabilities))


def calculate_debt_ratio(
    total_liabilities: Decimal,
    total_equity: Decimal,
) -> Decimal | None:
    """부채비율 = 총부채 / 자기자본 x 100 (퍼센트)."""
    return _safe_ratio(
        _to_decimal(total_liabilities),
        _to_decimal(total_equity),
        Decimal(100),
    )


def calculate_equity_ratio(
    total_equity: Decimal,
    total_assets: Decimal,
) -> Decimal | None:
    """자기자본비율 = 자기자본 / 총자산 x 100 (퍼센트)."""
    return _safe_ratio(
        _to_decimal(total_equity),
        _to_decimal(total_assets),
        Decimal(100),
    )


def calculate_roa(
    net_income: Decimal,
    total_assets: Decimal,
) -> Decimal | None:
    """ROA = 당기순이익 / 총자산 x 100 (퍼센트)."""
    return _safe_ratio(
        _to_decimal(net_income),
        _to_decimal(total_assets),
        Decimal(100),
    )


def calculate_roe(
    net_income: Decimal,
    total_equity: Decimal,
) -> Decimal | None:
    """ROE = 당기순이익 / 자기자본 x 100 (퍼센트)."""
    return _safe_ratio(
        _to_decimal(net_income),
        _to_decimal(total_equity),
        Decimal(100),
    )


class FinancialRatioService:
    """재무비율 분석 비즈니스 로직.

    제출된 분개전표를 집계하여 재무상태표/손익계산서 항목을 도출하고,
    5대 재무비율을 자동 산출하여 FinancialRatioReport로 저장한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._account_repo = Repository("accounts", tenant_id=tenant_id)
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)
        self._report_repo = Repository("financial_ratio_reports", tenant_id=tenant_id)

    def analyze_ratios(
        self,
        period_start: date,
        period_end: date,
    ) -> dict[str, Any]:
        """기간별 재무비율을 분석한다.

        Args:
            period_start: 분석 시작일
            period_end: 분석 종료일

        Returns:
            {"snapshot": {계정 합계}, "ratios": {5대 비율}, "period": {...}}
        """
        # 1. 계정과목 마스터 로드 (유동/비유동 분류)
        accounts = self._account_repo.find_many({}, limit=10000)
        account_meta: dict[str, dict[str, Any]] = {}
        for acc in accounts:
            name = acc.get("account_name", "")
            account_meta[name] = {
                "type": acc.get("account_type", ""),
                "is_current": self._infer_current(acc),
            }

        # 2. 기간 내 제출 전표 집계
        start_dt = datetime(period_start.year, period_start.month, period_start.day, tzinfo=UTC)
        end_dt = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, tzinfo=UTC)
        entries = self._je_repo.find_many(
            {
                "posting_date": {"$gte": start_dt, "$lte": end_dt},
                "docstatus": DocStatus.SUBMITTED,
            },
            limit=50000,
        )

        snapshot = self._build_snapshot(entries, account_meta)

        # 3. 5대 재무비율 산출
        ratios = {
            "current_ratio": calculate_current_ratio(
                snapshot["current_assets"],
                snapshot["current_liabilities"],
            ),
            "debt_ratio": calculate_debt_ratio(
                snapshot["total_liabilities"],
                snapshot["total_equity"],
            ),
            "equity_ratio": calculate_equity_ratio(
                snapshot["total_equity"],
                snapshot["total_assets"],
            ),
            "roa": calculate_roa(
                snapshot["net_income"],
                snapshot["total_assets"],
            ),
            "roe": calculate_roe(
                snapshot["net_income"],
                snapshot["total_equity"],
            ),
        }

        result = {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "snapshot": snapshot,
            "ratios": ratios,
            "interpretation": self._interpret(ratios),
        }

        logger.info(
            "재무비율 분석 완료: %s ~ %s, 유동비율=%s, ROE=%s",
            period_start,
            period_end,
            ratios["current_ratio"],
            ratios["roe"],
        )

        return result

    def save_ratio_report(
        self,
        report_name: str,
        period_start: date,
        period_end: date,
    ) -> str:
        """분석 결과를 FinancialRatioReport 문서로 저장한다.

        Returns:
            저장된 문서 ID
        """
        result = self.analyze_ratios(period_start, period_end)
        ratios = result["ratios"]

        report_id = generate_name("FRR", tenant_id=self._tenant_id)
        report = FinancialRatioReport(
            _id=report_id,
            report_name=report_name,
            period=f"{period_start.isoformat()}~{period_end.isoformat()}",
            current_ratio=ratios["current_ratio"] or Decimal(0),
            debt_ratio=ratios["debt_ratio"] or Decimal(0),
            roe=ratios["roe"] or Decimal(0),
            roa=ratios["roa"] or Decimal(0),
            tenant_id=self._tenant_id,
        )
        self._report_repo.insert(report)

        logger.info("재무비율 보고서 저장: %s (%s)", report_id, report_name)
        return report_id

    # -- 내부 헬퍼 --

    def _infer_current(self, account_doc: dict[str, Any]) -> bool:
        """계정과목이 유동성 항목인지 추론한다.

        우선순위:
        1. is_current 플래그 (마스터에 명시된 경우)
        2. 계정과목명에 "유동" 키워드 포함
        """
        if "is_current" in account_doc:
            return bool(account_doc["is_current"])
        name = account_doc.get("account_name", "")
        return "유동" in name and "비유동" not in name

    def _build_snapshot(
        self,
        entries: list[dict[str, Any]],
        account_meta: dict[str, dict[str, Any]],
    ) -> dict[str, Decimal]:
        """전표 집계로 재무상태표 + 손익계산서 스냅샷을 생성한다."""
        snapshot: dict[str, Decimal] = {
            "total_assets": Decimal(0),
            "current_assets": Decimal(0),
            "total_liabilities": Decimal(0),
            "current_liabilities": Decimal(0),
            "total_equity": Decimal(0),
            "total_income": Decimal(0),
            "total_expense": Decimal(0),
            "net_income": Decimal(0),
        }

        for entry in entries:
            for item in entry.get("items", []):
                account = item.get("account", "")
                meta = account_meta.get(account, {})
                acc_type = item.get("account_type") or meta.get("type", "")
                is_current = meta.get("is_current", False)

                debit = _to_decimal(item.get("debit", 0))
                credit = _to_decimal(item.get("credit", 0))

                if acc_type == "asset":
                    net = debit - credit
                    snapshot["total_assets"] += net
                    if is_current:
                        snapshot["current_assets"] += net
                elif acc_type == "liability":
                    net = credit - debit
                    snapshot["total_liabilities"] += net
                    if is_current:
                        snapshot["current_liabilities"] += net
                elif acc_type == "equity":
                    snapshot["total_equity"] += credit - debit
                elif acc_type == "income":
                    snapshot["total_income"] += credit - debit
                elif acc_type == "expense":
                    snapshot["total_expense"] += debit - credit

        snapshot["net_income"] = snapshot["total_income"] - snapshot["total_expense"]
        return snapshot

    def _interpret(self, ratios: dict[str, Decimal | None]) -> dict[str, str]:
        """5대 비율의 정성적 해석을 반환한다 (한국 일반 기준)."""
        interpretation: dict[str, str] = {}

        cr = ratios.get("current_ratio")
        if cr is None:
            interpretation["current_ratio"] = "데이터 부족"
        elif cr >= Decimal("2.00"):
            interpretation["current_ratio"] = "양호 (200% 이상)"
        elif cr >= Decimal("1.00"):
            interpretation["current_ratio"] = "주의 (100~200%)"
        else:
            interpretation["current_ratio"] = "위험 (100% 미만)"

        dr = ratios.get("debt_ratio")
        if dr is None:
            interpretation["debt_ratio"] = "데이터 부족"
        elif dr <= Decimal(100):
            interpretation["debt_ratio"] = "안정 (100% 이하)"
        elif dr <= Decimal(200):
            interpretation["debt_ratio"] = "보통 (100~200%)"
        else:
            interpretation["debt_ratio"] = "주의 (200% 초과)"

        roe = ratios.get("roe")
        if roe is None:
            interpretation["roe"] = "데이터 부족"
        elif roe >= Decimal(15):
            interpretation["roe"] = "우수 (15% 이상)"
        elif roe >= Decimal(5):
            interpretation["roe"] = "양호 (5~15%)"
        else:
            interpretation["roe"] = "저조 (5% 미만)"

        return interpretation
