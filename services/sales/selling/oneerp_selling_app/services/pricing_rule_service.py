"""가격 규칙 엔진 — selling 서비스용 래퍼 + 확장 엔진.

core의 PricingRuleService를 selling 컬렉션(pricing_rules)으로 초기화하여
기존 apply_rules 경로의 호환성을 유지한다.

selling 전용 확장:
- find_applicable_rules: 컨텍스트(item/customer/group/territory/qty/date) 기반 후보 탐색
- resolve_best_rule: 우선순위·구체성·최신성 기반 단일 규칙 해소
- calculate_final_rate: 할인 유형(Rate/Discount Percentage/Discount Amount) 적용

L2 비즈니스 룰 매핑:
- BR-SELL-014: 가격 규칙 우선순위 (여러 규칙 매칭 시 구체적·우선순위·최신 규칙이 이김)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from oneerp_core.pricing import PricingRuleService as _CorePricingRuleService
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# selling 서비스 전용 컬렉션명
_SELLING_PRICING_RULES_COLLECTION = "pricing_rules"

# 구체성 점수 — 값이 클수록 더 구체적인 매칭 (= 우선 선택)
_SPECIFICITY_CUSTOMER = 3
_SPECIFICITY_CUSTOMER_GROUP = 2
_SPECIFICITY_TERRITORY = 1
_SPECIFICITY_NONE = 0


class PricingRuleService(_CorePricingRuleService):
    """판매용 가격 규칙 서비스.

    기존 인터페이스(tenant_id만 받는 생성자)를 유지하면서 selling 고유의
    조건부 할인/수량 구간/기간 중첩 해소 로직을 확장 메서드로 제공한다.

    apply_rules()의 party 파라미터에 고객 ID를 전달하면 된다.
    """

    def __init__(self, tenant_id: str) -> None:
        repo = Repository(_SELLING_PRICING_RULES_COLLECTION, tenant_id=tenant_id)
        super().__init__(rule_repo=repo)
        self._tenant_id = tenant_id

    # -----------------------------------------------------------------
    # 1) 적용 가능 규칙 탐색
    # -----------------------------------------------------------------

    def find_applicable_rules(
        self,
        *,
        item_code: str,
        customer: str | None = None,
        customer_group: str | None = None,
        territory: str | None = None,
        qty: Decimal = Decimal(1),
        transaction_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """주어진 컨텍스트에 적용 가능한 모든 가격 규칙을 반환한다.

        규칙은 우선순위 정렬하지 않고, 매칭된 순서대로 반환한다. 실제 해소는
        `resolve_best_rule`에서 수행한다. 저장소에서 활성 규칙만 가져오고,
        각 규칙의 적용 대상·거래처·수량·기간 조건을 메모리에서 필터링한다.

        Args:
            item_code: 품목 코드.
            customer: 고객 ID (선택).
            customer_group: 고객 그룹 (선택).
            territory: 영업 지역 (선택).
            qty: 수량.
            transaction_date: 거래 일자. None이면 오늘.

        Returns:
            조건을 만족하는 규칙 dict 리스트.
        """
        when = transaction_date or datetime.now(tz=UTC).date()
        # 활성 규칙만 조회 (저장소 필터)
        rules = self._rule_repo.find_many({"is_active": True}, limit=1000)

        candidates: list[dict[str, Any]] = []
        for rule in rules:
            if not self._matches_apply_target(rule, item_code):
                continue
            if not self._matches_party(rule, customer, customer_group, territory):
                continue
            if not self._matches_qty_range(rule, qty):
                continue
            if not self._matches_date_range(rule, when):
                continue
            candidates.append(rule)

        logger.debug(
            "적용 가능 규칙 %d건 탐색 (item=%s, customer=%s, qty=%s)",
            len(candidates),
            item_code,
            customer,
            qty,
        )
        return candidates

    # -----------------------------------------------------------------
    # 2) 최적 규칙 해소
    # -----------------------------------------------------------------

    def resolve_best_rule(
        self,
        rules: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """기간 중첩·구체성·우선순위로 단일 최적 규칙을 결정한다.

        정렬 키(우선 순위):
        1. 구체성이 높은 규칙(customer > customer_group > territory > none)
        2. priority 값이 낮은 규칙(1 > 2 > 3)
        3. valid_from이 가장 최근(최근 등록) 규칙

        Args:
            rules: 후보 규칙 리스트.

        Returns:
            최적 규칙 dict, 후보가 비었으면 None.
        """
        if not rules:
            return None

        def _sort_key(rule: dict[str, Any]) -> tuple[int, int, str]:
            # 구체성은 내림차순이 우선이므로 음수로 뒤집어 오름차순 정렬에 사용
            specificity_score = -self._specificity(rule)
            # priority는 낮을수록 우선이므로 그대로 오름차순
            priority_value = int(rule.get("priority") or 0)
            # valid_from은 최신(=더 큰 문자열/날짜)이 우선이므로 음수 대신
            # 역정렬 문자열을 사용한다. ISO date 문자열은 그대로 내림차순.
            valid_from_key = _invert_date_key(rule.get("valid_from"))
            return (specificity_score, priority_value, valid_from_key)

        sorted_rules = sorted(rules, key=_sort_key)
        best = sorted_rules[0]
        logger.debug("최적 규칙 해소: %s", best.get("_id"))
        return best

    # -----------------------------------------------------------------
    # 3) 최종 단가 계산
    # -----------------------------------------------------------------

    def calculate_final_rate(
        self,
        *,
        item_code: str,
        base_rate: Decimal,
        customer: str | None = None,
        customer_group: str | None = None,
        territory: str | None = None,
        qty: Decimal = Decimal(1),
        transaction_date: date | None = None,
    ) -> tuple[Decimal, dict[str, Any] | None]:
        """기본 단가에 가격 규칙을 적용하여 최종 단가와 적용 규칙을 반환한다.

        해소 순서:
        1. `find_applicable_rules`로 후보 수집
        2. `resolve_best_rule`로 단일 규칙 결정
        3. `rate_or_discount` 유형별로 최종 단가 계산

        Args:
            item_code: 품목 코드.
            base_rate: 기본 단가.
            customer: 고객 ID.
            customer_group: 고객 그룹.
            territory: 영업 지역.
            qty: 수량.
            transaction_date: 거래 일자.

        Returns:
            (최종 단가, 적용 규칙). 규칙이 없으면 (base_rate, None).
        """
        candidates = self.find_applicable_rules(
            item_code=item_code,
            customer=customer,
            customer_group=customer_group,
            territory=territory,
            qty=qty,
            transaction_date=transaction_date,
        )
        best = self.resolve_best_rule(candidates)
        if best is None:
            return base_rate, None

        final_rate = self._apply_rule_to_rate(best, base_rate)
        return final_rate, best

    # =================================================================
    # 내부 헬퍼 — 조건 매칭
    # =================================================================

    @staticmethod
    def _matches_apply_target(rule: dict[str, Any], item_code: str) -> bool:
        """applicable_for 필드에 따른 적용 대상 매칭."""
        applicable_for = rule.get("applicable_for", "item_code")
        applicable_for_value = rule.get("applicable_for_value")

        # 기본은 item_code 매칭. item_group/brand 등은 컨텍스트 확장 시 추가.
        if applicable_for == "item_code":
            return applicable_for_value == item_code

        # 미지원 타입은 지금 시점에서는 매칭시키지 않는다(보수적).
        return False

    @staticmethod
    def _matches_party(
        rule: dict[str, Any],
        customer: str | None,
        customer_group: str | None,
        territory: str | None,
    ) -> bool:
        """거래처 관련 조건(customer/customer_group/territory) 매칭.

        규칙의 각 필드가 None이면 무조건 통과(전 고객 대상). 지정되어 있으면
        컨텍스트와 정확히 일치해야 매칭된다.
        """
        rule_customer = rule.get("customer")
        if rule_customer is not None and rule_customer != customer:
            return False

        rule_group = rule.get("customer_group")
        if rule_group is not None and rule_group != customer_group:
            return False

        rule_territory = rule.get("territory")
        return not (rule_territory is not None and rule_territory != territory)

    @staticmethod
    def _matches_qty_range(rule: dict[str, Any], qty: Decimal) -> bool:
        """min_qty <= qty <= max_qty 매칭. 필드가 없거나 None이면 범위 무제한."""
        min_qty_raw = rule.get("min_qty", 0)
        max_qty_raw = rule.get("max_qty")

        try:
            min_qty = Decimal(str(min_qty_raw))
        except TypeError, ValueError, InvalidOperation:
            min_qty = Decimal(0)

        if qty < min_qty:
            return False

        if max_qty_raw is not None:
            try:
                max_qty = Decimal(str(max_qty_raw))
            except TypeError, ValueError, InvalidOperation:
                return True
            if qty > max_qty:
                return False

        return True

    @staticmethod
    def _matches_date_range(rule: dict[str, Any], when: date) -> bool:
        """valid_from <= when <= valid_upto 매칭."""
        valid_from = _coerce_date(rule.get("valid_from"))
        valid_upto = _coerce_date(rule.get("valid_upto"))

        if valid_from is not None and when < valid_from:
            return False
        return not (valid_upto is not None and when > valid_upto)

    @staticmethod
    def _specificity(rule: dict[str, Any]) -> int:
        """규칙이 얼마나 구체적인지 점수화한다 (큰 숫자 = 더 구체적)."""
        if rule.get("customer"):
            return _SPECIFICITY_CUSTOMER
        if rule.get("customer_group"):
            return _SPECIFICITY_CUSTOMER_GROUP
        if rule.get("territory"):
            return _SPECIFICITY_TERRITORY
        return _SPECIFICITY_NONE

    @staticmethod
    def _apply_rule_to_rate(rule: dict[str, Any], base_rate: Decimal) -> Decimal:
        """선택된 규칙을 base_rate에 적용하여 최종 단가를 반환한다."""
        mode = rule.get("rate_or_discount", "Discount Percentage")

        if mode == "Rate":
            rate_value = rule.get("rate", 0)
            return _to_decimal(rate_value)

        if mode == "Discount Amount":
            discount_amount = _to_decimal(rule.get("discount_amount", 0))
            # 음수 방지
            result = base_rate - discount_amount
            return result if result > 0 else Decimal(0)

        # 기본: Discount Percentage
        discount_percentage = _to_decimal(rule.get("discount_percentage", 0))
        factor = Decimal(1) - (discount_percentage / Decimal(100))
        return base_rate * factor


# =====================================================================
# 모듈 레벨 유틸리티
# =====================================================================


def _to_decimal(value: Any) -> Decimal:
    """임의 타입을 Decimal로 안전 변환. 변환 실패 시 0을 반환한다."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal(0)
    try:
        return Decimal(str(value))
    except TypeError, ValueError, InvalidOperation:
        return Decimal(0)


def _coerce_date(value: Any) -> date | None:
    """문자열/datetime/date 혼합 입력을 date로 정규화한다."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            # datetime 문자열(예: 'YYYY-MM-DDTHH:MM:SS')인 경우
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                return None
    return None


def _invert_date_key(value: Any) -> str:
    """정렬 키 — valid_from이 최신일수록 앞에 오도록 문자열 역변환.

    ISO date 문자열은 알파벳 내림차순이 곧 날짜 내림차순이므로, 각 문자를
    역 서열(chr(255 - ord))로 변환해 sort()의 오름차순이 날짜 내림차순이
    되게 만든다.
    """
    parsed = _coerce_date(value)
    if parsed is None:
        # None은 가장 오래된 것으로 취급 → 정렬 키의 끝으로 밀림
        return "\x00"
    iso = parsed.isoformat()
    return "".join(chr(255 - ord(ch)) for ch in iso)
