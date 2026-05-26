"""연령분석 서비스 — 매출채권/매입채무 연령 분석 및 대손충당금 추정.

L2 비즈니스 룰 매핑:
- BR-ACCT-013 확장: 미수금 연령 구간 분석 (0-30 / 31-60 / 61-90 / 91-120 / 120+ 일)
- 한국 K-IFRS 1109 (금융상품) 기대신용손실(ECL) 모델 기반 단순화 충당율 적용
- 부가가치세법상 대손세액공제 (5년 경과·1천만원 이하 등) 후속 연계 가능

설계 메모:
- 본 서비스는 읽기 전용 집계 분석. 분개를 생성하지 않는다.
- group_by_customer/supplier 옵션으로 거래처별 잔액 드릴다운 지원.
- 충당율은 사내 회계정책에 따라 주입 가능 (provision_rates 파라미터).
- 산업별 차이가 크므로 기본값은 보수적이지 않은 평균치 적용.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# K-IFRS 1109 (기대신용손실) 단순화 — 한국 업계 평균 기준 기본 충당율
# 실제 적용 시 회사별 회계정책에 따라 provision_rates 인자로 재정의 가능.
DEFAULT_PROVISION_RATES: dict[str, Decimal] = {
    "미도래": Decimal(0),
    "0-30일": Decimal(0),
    "31-60일": Decimal("0.01"),
    "61-90일": Decimal("0.05"),
    "91-120일": Decimal("0.20"),
    "120일 초과": Decimal("0.50"),
    "미분류": Decimal("0.02"),
}

# 표준 연령 구간 (한국 재무보고서 관행)
AGING_BUCKETS = (
    "미도래",
    "0-30일",
    "31-60일",
    "61-90일",
    "91-120일",
    "120일 초과",
    "미분류",
)


def classify_aging_bucket(days_overdue: int) -> str:
    """경과일수를 표준 연령 구간으로 분류한다.

    Args:
        days_overdue: 만기일 기준 경과일수 (음수=미도래)

    Returns:
        구간 라벨. 0 이하는 미도래, 1~30은 0-30일, ..., 121+는 120일 초과
    """
    if days_overdue <= 0:
        return "미도래"
    if days_overdue <= 30:
        return "0-30일"
    if days_overdue <= 60:
        return "31-60일"
    if days_overdue <= 90:
        return "61-90일"
    if days_overdue <= 120:
        return "91-120일"
    return "120일 초과"


def _to_decimal(value: Any) -> Decimal:
    """다양한 입력을 Decimal로 안전하게 변환한다."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal(0)
    return Decimal(str(value))


def _parse_due_date(value: Any) -> date | None:
    """due_date 필드를 date 객체로 변환한다. None이면 None."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


class AgedAnalysisService:
    """매출채권/매입채무 연령분석 비즈니스 로직.

    재무팀의 채권/채무 회수·지급 관리와
    K-IFRS 1109 기대신용손실 충당금 추정에 활용된다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._ar_repo = Repository("accounts_receivable", tenant_id=tenant_id)
        self._ap_repo = Repository("accounts_payable", tenant_id=tenant_id)

    def analyze_receivables(
        self,
        as_of_date: date,
        *,
        group_by_customer: bool = False,
    ) -> dict[str, Any]:
        """매출채권 연령분석을 수행한다.

        Args:
            as_of_date: 기준일 (보통 월말 또는 보고일)
            group_by_customer: True이면 고객별 집계 결과 포함

        Returns:
            연령 구간별 잔액 + 총합 (+ 선택적 고객별 집계)
        """
        records = self._ar_repo.find_many({}, limit=50000)
        return self._analyze_records(
            records=records,
            as_of_date=as_of_date,
            party_field="customer",
            include_party_breakdown=group_by_customer,
            party_breakdown_key="by_customer",
        )

    def analyze_payables(
        self,
        as_of_date: date,
        *,
        group_by_supplier: bool = False,
    ) -> dict[str, Any]:
        """매입채무 연령분석을 수행한다.

        Args:
            as_of_date: 기준일
            group_by_supplier: True이면 공급사별 집계 결과 포함
        """
        records = self._ap_repo.find_many({}, limit=50000)
        return self._analyze_records(
            records=records,
            as_of_date=as_of_date,
            party_field="supplier",
            include_party_breakdown=group_by_supplier,
            party_breakdown_key="by_supplier",
        )

    def estimate_bad_debt_provision(
        self,
        as_of_date: date,
        provision_rates: dict[str, Decimal] | None = None,
    ) -> dict[str, Any]:
        """매출채권 기준 대손충당금 추정 (K-IFRS 1109 단순화).

        구간별 잔액에 충당율을 곱하여 합산한 추정 손실 충당금을 반환한다.

        Args:
            as_of_date: 기준일
            provision_rates: 사용자 정의 충당율 (None이면 DEFAULT_PROVISION_RATES)

        Returns:
            {"total_provision": Decimal, "by_bucket": {bucket: provision_amount}, ...}
        """
        rates = provision_rates if provision_rates is not None else DEFAULT_PROVISION_RATES

        analysis = self.analyze_receivables(as_of_date=as_of_date)
        buckets = analysis["buckets"]

        provision_by_bucket: dict[str, Decimal] = {}
        total_provision = Decimal(0)

        for bucket_name, bucket_data in buckets.items():
            amount: Decimal = bucket_data["amount"]
            rate = rates.get(bucket_name, Decimal(0))
            provision = (amount * rate).quantize(Decimal(1))
            provision_by_bucket[bucket_name] = provision
            total_provision += provision

        logger.info(
            "대손충당금 추정: 기준일=%s, 총 충당금=%s",
            as_of_date.isoformat(),
            total_provision,
        )

        return {
            "as_of_date": as_of_date.isoformat(),
            "total_outstanding": analysis["total_outstanding"],
            "total_provision": total_provision,
            "by_bucket": provision_by_bucket,
            "applied_rates": {k: str(v) for k, v in rates.items()},
        }

    # -- 내부 헬퍼 --

    def _analyze_records(
        self,
        records: list[dict[str, Any]],
        as_of_date: date,
        party_field: str,
        *,
        include_party_breakdown: bool,
        party_breakdown_key: str,
    ) -> dict[str, Any]:
        """공통 연령 분류·집계 로직 (AR/AP 공유)."""
        # 구간별 초기화
        buckets: dict[str, dict[str, Any]] = {
            name: {"amount": Decimal(0), "count": 0, "items": []} for name in AGING_BUCKETS
        }

        total = Decimal(0)
        party_totals: dict[str, dict[str, Any]] = {}

        for rec in records:
            amount = _to_decimal(rec.get("outstanding_amount", 0))
            if amount == 0:
                continue

            due = _parse_due_date(rec.get("due_date"))
            party = str(rec.get(party_field, ""))

            if due is None:
                bucket_name = "미분류"
            else:
                days_overdue = (as_of_date - due).days
                bucket_name = classify_aging_bucket(days_overdue)

            buckets[bucket_name]["amount"] += amount
            buckets[bucket_name]["count"] += 1
            buckets[bucket_name]["items"].append(
                {
                    party_field: party,
                    "outstanding_amount": amount,
                    "due_date": due.isoformat() if due else None,
                    "invoice_id": rec.get("invoice_id", ""),
                }
            )
            total += amount

            if include_party_breakdown:
                party_data = party_totals.setdefault(
                    party,
                    {"total": Decimal(0), "buckets": {b: Decimal(0) for b in AGING_BUCKETS}},
                )
                party_data["total"] += amount
                party_data["buckets"][bucket_name] += amount

        result: dict[str, Any] = {
            "as_of_date": as_of_date.isoformat(),
            "total_outstanding": total,
            "buckets": buckets,
        }
        if include_party_breakdown:
            result[party_breakdown_key] = party_totals

        logger.info(
            "%s 연령분석 완료: 총 %s원 (구간 수: %d)",
            "AR" if party_field == "customer" else "AP",
            total,
            len(AGING_BUCKETS),
        )

        return result
