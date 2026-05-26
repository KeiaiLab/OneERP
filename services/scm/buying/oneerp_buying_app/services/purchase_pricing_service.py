"""구매 가격 규칙 서비스 — 구매 문서에 가격 규칙을 적용한다.

core의 PricingRuleService를 구매용 컬렉션(purchase_pricing_rules)으로 초기화하여
공급업체별 할인/특별가를 자동 적용한다.
"""

from __future__ import annotations

from oneerp_core.pricing import PricingRuleService as _CorePricingRuleService
from oneerp_core.repository import Repository

# 구매 서비스 전용 가격 규칙 컬렉션명
_PURCHASE_PRICING_RULES_COLLECTION = "purchase_pricing_rules"


class PurchasePricingService(_CorePricingRuleService):
    """구매용 가격 규칙 서비스.

    공급업체(supplier)별 할인 규칙을 적용한다.
    apply_rules()의 party 파라미터에 공급업체 ID를 전달하면 된다.
    """

    def __init__(self, tenant_id: str) -> None:
        repo = Repository(_PURCHASE_PRICING_RULES_COLLECTION, tenant_id=tenant_id)
        super().__init__(rule_repo=repo)
        self._tenant_id = tenant_id
