"""구독관리 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

SubscriptionPlan, Subscription, SubscriptionInvoice, RecurringInvoice
엔티티를 EntityMeta로 선언한다.
구독 라이프사이클 로직(활성화/일시정지/해지/재개)은 routes/에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.recurring_invoice import (
    RecurringInvoice,
    RecurringInvoiceCreate,
    RecurringInvoiceUpdate,
)
from .models.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate
from .models.subscription_invoice import (
    SubscriptionInvoice,
    SubscriptionInvoiceCreate,
    SubscriptionInvoiceUpdate,
)
from .models.subscription_plan import (
    SubscriptionPlan,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
)

ENTITY_METAS: list[EntityMeta] = [
    # 마스터 데이터
    EntityMeta(
        collection="subscription_plans",
        prefix="SPL",
        api_path="/api/v1/subscriptions/plans",
        tag="구독 플랜",
        resource="subscription_plan",
        model=SubscriptionPlan,
        create_schema=SubscriptionPlanCreate,
        update_schema=SubscriptionPlanUpdate,
        archetype="master",
        not_found_message="구독 플랜을 찾을 수 없습니다",
    ),
    # 트랜잭션 문서
    EntityMeta(
        collection="subscriptions",
        prefix="SUB",
        api_path="/api/v1/subscriptions/items",
        tag="구독",
        resource="subscription",
        model=Subscription,
        create_schema=SubscriptionCreate,
        update_schema=SubscriptionUpdate,
        archetype="transaction",
        not_found_message="구독을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="subscription_invoices",
        prefix="SINV",
        api_path="/api/v1/subscriptions/invoices",
        tag="구독 청구",
        resource="subscription_invoice",
        model=SubscriptionInvoice,
        create_schema=SubscriptionInvoiceCreate,
        update_schema=SubscriptionInvoiceUpdate,
        archetype="transaction",
        not_found_message="구독 청구를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="recurring_invoices",
        prefix="RI",
        api_path="/api/v1/subscriptions/recurring-invoices",
        tag="정기 청구",
        resource="recurring_invoice",
        model=RecurringInvoice,
        create_schema=RecurringInvoiceCreate,
        update_schema=RecurringInvoiceUpdate,
        archetype="transaction",
        not_found_message="정기 청구를 찾을 수 없습니다",
    ),
]
