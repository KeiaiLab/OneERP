"""소득세 산출 서비스 — 간이세액표 기반 월 소득세 계산.

2026년 기준 근로소득 간이세액표(근사치)를 사용하여
월 급여에 대한 소득세와 지방소득세를 산출한다.

또한 ``calculate_income_tax_withholding``는 간이세액표가 아닌 누진세율 기반의
단순화 추정 알고리즘을 제공한다. 실제 정확한 간이세액표는 매우 복잡하므로
후속 사이클에서 표 로딩 방식으로 대체한다.
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal

logger = logging.getLogger(__name__)

# --- 누진세율 단순화 상수 (2026년 기준) -------------------------------------

# 연간 부양가족 인적공제 (인당)
_ANNUAL_DEPENDENT_DEDUCTION = Decimal(1500000)

# 누진세율 구간 — (상한_과세표준, 세율, 누진공제)
# 과세표준이 상한 이하면 해당 구간 세율 적용: 세액 = 과표 x 세율 - 누진공제
_PROGRESSIVE_BRACKETS: list[tuple[Decimal, Decimal, Decimal]] = [
    (Decimal(14000000), Decimal("0.06"), Decimal(0)),
    (Decimal(50000000), Decimal("0.15"), Decimal(1260000)),
    (Decimal(88000000), Decimal("0.24"), Decimal(5760000)),
    (Decimal(150000000), Decimal("0.35"), Decimal(15440000)),
    (Decimal(300000000), Decimal("0.38"), Decimal(19940000)),
    (Decimal(500000000), Decimal("0.40"), Decimal(25940000)),
    (Decimal(1000000000), Decimal("0.42"), Decimal(35940000)),
]
# 10억 초과 최고 세율 구간
_TOP_BRACKET_RATE = Decimal("0.45")
_TOP_BRACKET_DEDUCTION = Decimal(45940000)

# 지방소득세율 = 소득세 x 10%
_LOCAL_TAX_RATE = Decimal("0.1")


def _earned_income_deduction(annual_gross: Decimal) -> Decimal:
    """BR-PAY-009: 근로소득공제(연간) — 5단계 누진.

    - 500만원 이하 : 70% (최소 공제)
    - 500만~1,500만 : 350만 + (초과 x 40%)
    - 1,500만~4,500만 : 750만 + (초과 x 15%)
    - 4,500만~1억 : 1,200만 + (초과 x 5%)
    - 1억 초과 : 1,475만 + (초과 x 2%)
    """
    if annual_gross <= Decimal(0):
        return Decimal(0)
    if annual_gross <= Decimal(5000000):
        return annual_gross * Decimal("0.7")
    if annual_gross <= Decimal(15000000):
        return Decimal(3500000) + (annual_gross - Decimal(5000000)) * Decimal("0.4")
    if annual_gross <= Decimal(45000000):
        return Decimal(7500000) + (annual_gross - Decimal(15000000)) * Decimal("0.15")
    if annual_gross <= Decimal(100000000):
        return Decimal(12000000) + (annual_gross - Decimal(45000000)) * Decimal("0.05")
    return Decimal(14750000) + (annual_gross - Decimal(100000000)) * Decimal("0.02")


def _progressive_tax(taxable_base: Decimal) -> Decimal:
    """BR-PAY-010: 누진세율 계산 — 과세표준 → 산출세액.

    8단계 누진세율을 적용한다. 과세표준이 0 이하이면 0을 반환한다.
    """
    if taxable_base <= Decimal(0):
        return Decimal(0)

    for upper, rate, deduction in _PROGRESSIVE_BRACKETS:
        if taxable_base <= upper:
            return taxable_base * rate - deduction

    # 10억 초과 최고 세율 구간
    return taxable_base * _TOP_BRACKET_RATE - _TOP_BRACKET_DEDUCTION


# 간이세액표 (월급여 구간별 세액, 부양가족 1인 기준)
# (하한, 상한, 세액) — 상한은 exclusive
_SIMPLE_TAX_TABLE: list[tuple[float, float, float]] = [
    (0, 1_060_000, 0),
    (1_060_000, 1_500_000, 19_060),
    (1_500_000, 2_000_000, 40_250),
    (2_000_000, 2_500_000, 60_440),
    (2_500_000, 3_000_000, 81_630),
    (3_000_000, 3_500_000, 93_020),
    (3_500_000, 4_000_000, 132_220),
    (4_000_000, 5_000_000, 176_400),
    (5_000_000, 6_000_000, 264_600),
    (6_000_000, 7_000_000, 364_600),
    (7_000_000, 8_000_000, 484_600),
    (8_000_000, 10_000_000, 604_600),
    (10_000_000, 14_000_000, 904_600),
    (14_000_000, 28_000_000, 1_504_600),
    (28_000_000, 30_000_000, 2_204_600),
    (30_000_000, 45_000_000, 2_604_600),
    (45_000_000, 87_000_000, 5_004_600),
    (87_000_000, float("inf"), 9_004_600),
]

# 부양가족 추가 1인당 공제액 (월 기준)
_DEPENDENT_DEDUCTION_PER_PERSON = 12_500


class IncomeTaxService:
    """소득세 산출 서비스.

    간이세액표를 기반으로 월 소득세를 산출하고,
    부양가족 수에 따른 추가 공제를 적용한다.
    """

    @staticmethod
    def calculate_monthly_tax(gross_pay: float, dependents: int = 1) -> float:
        """BR-PAY-006: 소득세 간이세액표 기반 월 소득세 산출.

        18단계 구간별 세액을 조회하고, 부양가족 추가공제(인당 12,500원)를 적용한다.

        Args:
            gross_pay: 총 지급액 (월급여)
            dependents: 부양가족 수 (본인 포함, 최소 1)

        Returns:
            소득세 금액 (원 단위, 반올림)
        """
        if gross_pay <= 0:
            return 0.0

        # 간이세액표에서 기본 세액 조회
        base_tax = 0.0
        for lower, upper, tax_amount in _SIMPLE_TAX_TABLE:
            if lower <= gross_pay < upper:
                base_tax = tax_amount
                break

        # 부양가족 추가 공제 (본인 1인 제외)
        extra_dependents = max(0, dependents - 1)
        dependent_deduction = extra_dependents * _DEPENDENT_DEDUCTION_PER_PERSON

        # 최소 세액: 0
        tax = max(0.0, base_tax - dependent_deduction)

        logger.info(
            "소득세 산출: gross_pay=%s, dependents=%s, base_tax=%s, tax=%s",
            gross_pay,
            dependents,
            base_tax,
            tax,
        )

        return round(tax)

    @staticmethod
    def calculate_local_income_tax(income_tax: float) -> float:
        """BR-PAY-007: 지방소득세 산출 (소득세의 10%).

        Args:
            income_tax: 소득세 금액

        Returns:
            지방소득세 금액 (원 단위, 반올림)
        """
        return round(income_tax * 0.1)

    @staticmethod
    def calculate_income_tax_withholding(
        monthly_gross: Decimal,
        dependents: int = 1,
    ) -> tuple[Decimal, Decimal]:
        """BR-PAY-006: 소득세 원천징수 — 누진세율 단순 추정.

        ⚠️ **주의**: 본 메서드는 실제 근로소득 간이세액표(18단계)가 아닌
        단순화 추정 알고리즘을 제공한다. 정확한 간이세액표는
        ``calculate_monthly_tax`` 메서드를 사용해야 하며, 본 메서드는
        연말정산 미리보기, 간이 시뮬레이션, 계산기 등에 사용한다.

        알고리즘:
            1. 연간 추정 = 월급 x 12
            2. 과세표준 = 연간 추정 - 근로소득공제 - (부양가족 수 x 150만)
            3. 산출세액 = 과세표준 x 누진세율 (BR-PAY-010)
            4. 월 소득세 = 산출세액 / 12
            5. 지방소득세 = 소득세 x 10%

        Args:
            monthly_gross: 월 총지급액
            dependents: 부양가족 수 (본인 포함, 최소 1)

        Returns:
            (월 소득세, 월 지방소득세) 튜플 — 모두 원 단위 반올림

        Raises:
            ValueError: 월 지급액 또는 부양가족 수가 음수일 때
        """
        if monthly_gross < Decimal(0):
            raise ValueError("월 지급액은 0 이상이어야 합니다")
        if dependents < 0:
            raise ValueError("부양가족 수는 0 이상이어야 합니다")

        if monthly_gross == Decimal(0):
            return Decimal(0), Decimal(0)

        # 1. 연간 추정
        annual_gross = monthly_gross * Decimal(12)

        # 2. 근로소득공제
        earned_deduction = _earned_income_deduction(annual_gross)

        # 3. 인적공제 (부양가족 수 x 150만, 최소 1인 본인)
        effective_dependents = max(1, dependents)
        personal_deduction = Decimal(effective_dependents) * _ANNUAL_DEPENDENT_DEDUCTION

        # 4. 과세표준 (음수는 0으로 클램프)
        taxable_base = annual_gross - earned_deduction - personal_deduction
        if taxable_base < Decimal(0):
            taxable_base = Decimal(0)

        # 5. 누진세율 산출세액
        annual_tax = _progressive_tax(taxable_base)
        if annual_tax < Decimal(0):
            annual_tax = Decimal(0)

        # 6. 월 분할 → 원 단위 반올림
        monthly_tax = (annual_tax / Decimal(12)).quantize(Decimal(1), rounding=ROUND_HALF_UP)

        # 7. 지방소득세
        local_tax = (monthly_tax * _LOCAL_TAX_RATE).quantize(Decimal(1), rounding=ROUND_HALF_UP)

        logger.info(
            "원천징수 추정: monthly=%s, dependents=%s, monthly_tax=%s",
            monthly_gross,
            dependents,
            monthly_tax,
        )

        return monthly_tax, local_tax
