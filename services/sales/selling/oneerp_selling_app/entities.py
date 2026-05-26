"""Selling 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

28개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 11개 엔티티(quotations, price_lists, sales_partners, sales_orders,
delivery_notes, sales_invoices, sales_returns, blanket_orders, pos_transactions,
sales_analytics, pos_receipts)는 routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.commission_plan import CommissionPlan, CommissionPlanCreate, CommissionPlanUpdate
from .models.coupon_code import CouponCode, CouponCodeCreate, CouponCodeUpdate
from .models.customer import Customer, CustomerCreate, CustomerUpdate
from .models.customer_group import (
    CustomerGroup,
    CustomerGroupCreate,
    CustomerGroupUpdate,
)
from .models.drop_ship_order import DropShipOrder, DropShipOrderCreate, DropShipOrderUpdate
from .models.e_commerce_channel import (
    ECommerceChannel,
    ECommerceChannelCreate,
    ECommerceChannelUpdate,
)
from .models.export_declaration import (
    ExportDeclaration,
    ExportDeclarationCreate,
    ExportDeclarationUpdate,
)
from .models.loyalty_program import LoyaltyProgram, LoyaltyProgramCreate, LoyaltyProgramUpdate
from .models.marketplace_order import (
    MarketplaceOrder,
    MarketplaceOrderCreate,
    MarketplaceOrderUpdate,
)
from .models.pos_closing_entry import (
    POSClosingEntry,
    POSClosingEntryCreate,
    POSClosingEntryUpdate,
)
from .models.pos_payment_method import (
    POSPaymentMethod,
    POSPaymentMethodCreate,
    POSPaymentMethodUpdate,
)
from .models.pos_profile import POSProfile, POSProfileCreate, POSProfileUpdate
from .models.price_list import PriceList, PriceListCreate, PriceListUpdate
from .models.pricing_rule import PricingRule, PricingRuleCreate, PricingRuleUpdate
from .models.promotional_scheme import (
    PromotionalScheme,
    PromotionalSchemeCreate,
    PromotionalSchemeUpdate,
)
from .models.recurring_invoice import (
    RecurringInvoice,
    RecurringInvoiceCreate,
    RecurringInvoiceUpdate,
)
from .models.rental_item import RentalItem, RentalItemCreate, RentalItemUpdate
from .models.rental_order import RentalOrder, RentalOrderCreate, RentalOrderUpdate
from .models.rental_return import RentalReturn, RentalReturnCreate, RentalReturnUpdate
from .models.return_merchandise_authorization import (
    ReturnMerchandiseAuthorization,
    ReturnMerchandiseAuthorizationCreate,
    ReturnMerchandiseAuthorizationUpdate,
)
from .models.sales_commission import (
    SalesCommission,
    SalesCommissionCreate,
    SalesCommissionUpdate,
)
from .models.sales_partner import SalesPartner, SalesPartnerCreate, SalesPartnerUpdate
from .models.sales_person import SalesPerson, SalesPersonCreate, SalesPersonUpdate
from .models.sales_target import SalesTarget, SalesTargetCreate, SalesTargetUpdate
from .models.sales_team import SalesTeam, SalesTeamCreate, SalesTeamUpdate
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
from .models.territory import Territory, TerritoryCreate, TerritoryUpdate

# --- 마스터 데이터 (submit/cancel 없음) ---

CUSTOMER = EntityMeta(
    collection="customers",
    prefix="CUST",
    api_path="/api/v1/customers",
    tag="고객",
    resource="customer",
    model=Customer,
    create_schema=CustomerCreate,
    update_schema=CustomerUpdate,
    archetype="master",
    not_found_message="고객을 찾을 수 없습니다",
)

CUSTOMER_GROUP = EntityMeta(
    collection="customer_groups",
    prefix="CGR",
    api_path="/api/v1/customer-groups",
    tag="고객그룹",
    resource="customer_group",
    model=CustomerGroup,
    create_schema=CustomerGroupCreate,
    update_schema=CustomerGroupUpdate,
    archetype="master",
    not_found_message="고객그룹을 찾을 수 없습니다",
)

TERRITORY = EntityMeta(
    collection="territories",
    prefix="TER",
    api_path="/api/v1/territories",
    tag="영업구역",
    resource="territory",
    model=Territory,
    create_schema=TerritoryCreate,
    update_schema=TerritoryUpdate,
    archetype="master",
    not_found_message="영업구역을 찾을 수 없습니다",
)

SALES_PARTNER = EntityMeta(
    collection="sales_partners",
    prefix="SPAR",
    api_path="/api/v1/sales-partners",
    tag="판매 파트너",
    resource="sales_partner",
    model=SalesPartner,
    create_schema=SalesPartnerCreate,
    update_schema=SalesPartnerUpdate,
    archetype="master",
    not_found_message="판매 파트너를 찾을 수 없습니다",
)

PRICE_LIST = EntityMeta(
    collection="price_lists",
    prefix="PLT",
    api_path="/api/v1/price-lists",
    tag="가격표",
    resource="price_list",
    model=PriceList,
    create_schema=PriceListCreate,
    update_schema=PriceListUpdate,
    archetype="master",
    not_found_message="가격표를 찾을 수 없습니다",
)

PRICING_RULE = EntityMeta(
    collection="pricing_rules",
    prefix="PRC",
    api_path="/api/v1/pricing-rules",
    tag="가격규칙",
    resource="pricing_rule",
    model=PricingRule,
    create_schema=PricingRuleCreate,
    update_schema=PricingRuleUpdate,
    archetype="master",
    not_found_message="가격규칙을 찾을 수 없습니다",
)

POS_PROFILE = EntityMeta(
    collection="pos_profiles",
    prefix="POS",
    api_path="/api/v1/pos-profiles",
    tag="POS 프로필",
    resource="pos_profile",
    model=POSProfile,
    create_schema=POSProfileCreate,
    update_schema=POSProfileUpdate,
    archetype="master",
    not_found_message="POS 프로필을 찾을 수 없습니다",
)

POS_PAYMENT_METHOD = EntityMeta(
    collection="pos_payment_methods",
    prefix="POPM",
    api_path="/api/v1/pos-payment-methods",
    tag="POS 결제 수단",
    resource="pos_payment_method",
    model=POSPaymentMethod,
    create_schema=POSPaymentMethodCreate,
    update_schema=POSPaymentMethodUpdate,
    archetype="master",
    not_found_message="POS 결제 수단을 찾을 수 없습니다",
)

SALES_PERSON = EntityMeta(
    collection="sales_persons",
    prefix="SPER",
    api_path="/api/v1/sales-persons",
    tag="영업 사원",
    resource="sales_person",
    model=SalesPerson,
    create_schema=SalesPersonCreate,
    update_schema=SalesPersonUpdate,
    archetype="master",
    not_found_message="영업 사원을 찾을 수 없습니다",
)

SALES_TEAM = EntityMeta(
    collection="sales_teams",
    prefix="STEM",
    api_path="/api/v1/sales-teams",
    tag="영업 팀",
    resource="sales_team",
    model=SalesTeam,
    create_schema=SalesTeamCreate,
    update_schema=SalesTeamUpdate,
    archetype="master",
    not_found_message="영업 팀을 찾을 수 없습니다",
)

PROMOTIONAL_SCHEME = EntityMeta(
    collection="promotional_schemes",
    prefix="PRMO",
    api_path="/api/v1/promotional-schemes",
    tag="프로모션",
    resource="promotional_scheme",
    model=PromotionalScheme,
    create_schema=PromotionalSchemeCreate,
    update_schema=PromotionalSchemeUpdate,
    archetype="master",
    not_found_message="프로모션을 찾을 수 없습니다",
)

SALES_TARGET = EntityMeta(
    collection="sales_targets",
    prefix="STGT",
    api_path="/api/v1/sales-targets",
    tag="영업 목표",
    resource="sales_target",
    model=SalesTarget,
    create_schema=SalesTargetCreate,
    update_schema=SalesTargetUpdate,
    archetype="master",
    not_found_message="영업 목표를 찾을 수 없습니다",
)

COUPON_CODE = EntityMeta(
    collection="coupon_codes",
    prefix="COUP",
    api_path="/api/v1/coupon-codes",
    tag="쿠폰 코드",
    resource="coupon_code",
    model=CouponCode,
    create_schema=CouponCodeCreate,
    update_schema=CouponCodeUpdate,
    archetype="master",
    not_found_message="쿠폰 코드를 찾을 수 없습니다",
)

LOYALTY_PROGRAM = EntityMeta(
    collection="loyalty_programs",
    prefix="LYTY",
    api_path="/api/v1/loyalty-programs",
    tag="로열티 프로그램",
    resource="loyalty_program",
    model=LoyaltyProgram,
    create_schema=LoyaltyProgramCreate,
    update_schema=LoyaltyProgramUpdate,
    archetype="master",
    not_found_message="로열티 프로그램을 찾을 수 없습니다",
)

SUBSCRIPTION_PLAN = EntityMeta(
    collection="subscription_plans",
    prefix="SBPL",
    api_path="/api/v1/subscription-plans",
    tag="구독 플랜",
    resource="subscription_plan",
    model=SubscriptionPlan,
    create_schema=SubscriptionPlanCreate,
    update_schema=SubscriptionPlanUpdate,
    archetype="master",
    not_found_message="구독 플랜을 찾을 수 없습니다",
)

COMMISSION_PLAN = EntityMeta(
    collection="commission_plans",
    prefix="CMPL",
    api_path="/api/v1/commission-plans",
    tag="수수료 플랜",
    resource="commission_plan",
    model=CommissionPlan,
    create_schema=CommissionPlanCreate,
    update_schema=CommissionPlanUpdate,
    archetype="master",
    not_found_message="수수료 플랜을 찾을 수 없습니다",
)

E_COMMERCE_CHANNEL = EntityMeta(
    collection="e_commerce_channels",
    prefix="ECCH",
    api_path="/api/v1/e-commerce-channels",
    tag="이커머스 채널",
    resource="e_commerce_channel",
    model=ECommerceChannel,
    create_schema=ECommerceChannelCreate,
    update_schema=ECommerceChannelUpdate,
    archetype="master",
    not_found_message="이커머스 채널을 찾을 수 없습니다",
)

RENTAL_ITEM = EntityMeta(
    collection="rental_items",
    prefix="RNITM",
    api_path="/api/v1/rental-items",
    tag="렌탈 품목",
    resource="rental_item",
    model=RentalItem,
    create_schema=RentalItemCreate,
    update_schema=RentalItemUpdate,
    archetype="master",
    not_found_message="렌탈 품목을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 (submit/cancel 포함) ---

POS_CLOSING_ENTRY = EntityMeta(
    collection="pos_closing_entries",
    prefix="POSC",
    api_path="/api/v1/pos-closing-entries",
    tag="POS 마감",
    resource="pos_closing_entry",
    model=POSClosingEntry,
    create_schema=POSClosingEntryCreate,
    update_schema=POSClosingEntryUpdate,
    archetype="transaction",
    not_found_message="POS 마감을 찾을 수 없습니다",
)

SUBSCRIPTION = EntityMeta(
    collection="subscriptions",
    prefix="SUBS",
    api_path="/api/v1/subscriptions",
    tag="구독",
    resource="subscription",
    model=Subscription,
    create_schema=SubscriptionCreate,
    update_schema=SubscriptionUpdate,
    archetype="transaction",
    not_found_message="구독을 찾을 수 없습니다",
)

SUBSCRIPTION_INVOICE = EntityMeta(
    collection="subscription_invoices",
    prefix="SINV",
    api_path="/api/v1/subscription-invoices",
    tag="구독 청구서",
    resource="subscription_invoice",
    model=SubscriptionInvoice,
    create_schema=SubscriptionInvoiceCreate,
    update_schema=SubscriptionInvoiceUpdate,
    archetype="transaction",
    not_found_message="구독 청구서를 찾을 수 없습니다",
)

RECURRING_INVOICE = EntityMeta(
    collection="recurring_invoices",
    prefix="RINV",
    api_path="/api/v1/recurring-invoices",
    tag="반복 청구서",
    resource="recurring_invoice",
    model=RecurringInvoice,
    create_schema=RecurringInvoiceCreate,
    update_schema=RecurringInvoiceUpdate,
    archetype="transaction",
    not_found_message="반복 청구서를 찾을 수 없습니다",
)

SALES_COMMISSION = EntityMeta(
    collection="sales_commissions",
    prefix="SCOM",
    api_path="/api/v1/sales-commissions",
    tag="판매 수수료",
    resource="sales_commission",
    model=SalesCommission,
    create_schema=SalesCommissionCreate,
    update_schema=SalesCommissionUpdate,
    archetype="transaction",
    not_found_message="판매 수수료를 찾을 수 없습니다",
)

DROP_SHIP_ORDER = EntityMeta(
    collection="drop_ship_orders",
    prefix="DSO",
    api_path="/api/v1/drop-ship-orders",
    tag="직배송 주문",
    resource="drop_ship_order",
    model=DropShipOrder,
    create_schema=DropShipOrderCreate,
    update_schema=DropShipOrderUpdate,
    archetype="transaction",
    not_found_message="직배송 주문을 찾을 수 없습니다",
)

MARKETPLACE_ORDER = EntityMeta(
    collection="marketplace_orders",
    prefix="MKTO",
    api_path="/api/v1/marketplace-orders",
    tag="마켓플레이스 주문",
    resource="marketplace_order",
    model=MarketplaceOrder,
    create_schema=MarketplaceOrderCreate,
    update_schema=MarketplaceOrderUpdate,
    archetype="transaction",
    not_found_message="마켓플레이스 주문을 찾을 수 없습니다",
)

RENTAL_ORDER = EntityMeta(
    collection="rental_orders",
    prefix="RNORD",
    api_path="/api/v1/rental-orders",
    tag="렌탈 주문",
    resource="rental_order",
    model=RentalOrder,
    create_schema=RentalOrderCreate,
    update_schema=RentalOrderUpdate,
    archetype="transaction",
    not_found_message="렌탈 주문을 찾을 수 없습니다",
)

RENTAL_RETURN = EntityMeta(
    collection="rental_returns",
    prefix="RNRET",
    api_path="/api/v1/rental-returns",
    tag="렌탈 반납",
    resource="rental_return",
    model=RentalReturn,
    create_schema=RentalReturnCreate,
    update_schema=RentalReturnUpdate,
    archetype="transaction",
    not_found_message="렌탈 반납을 찾을 수 없습니다",
)

RETURN_MERCHANDISE_AUTHORIZATION = EntityMeta(
    collection="return_merchandise_authorizations",
    prefix="RMA",
    api_path="/api/v1/return-merchandise-authorizations",
    tag="반품 승인",
    resource="return_merchandise_authorization",
    model=ReturnMerchandiseAuthorization,
    create_schema=ReturnMerchandiseAuthorizationCreate,
    update_schema=ReturnMerchandiseAuthorizationUpdate,
    archetype="transaction",
    not_found_message="반품 승인을 찾을 수 없습니다",
)

EXPORT_DECLARATION = EntityMeta(
    collection="export_declarations",
    prefix="EXPD",
    api_path="/api/v1/export-declarations",
    tag="수출 신고",
    resource="export_declaration",
    model=ExportDeclaration,
    create_schema=ExportDeclarationCreate,
    update_schema=ExportDeclarationUpdate,
    archetype="transaction",
    not_found_message="수출 신고를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    CUSTOMER,
    CUSTOMER_GROUP,
    TERRITORY,
    PRICING_RULE,
    POS_PROFILE,
    POS_PAYMENT_METHOD,
    SALES_PERSON,
    SALES_TEAM,
    PROMOTIONAL_SCHEME,
    SALES_TARGET,
    COUPON_CODE,
    LOYALTY_PROGRAM,
    SUBSCRIPTION_PLAN,
    COMMISSION_PLAN,
    E_COMMERCE_CHANNEL,
    RENTAL_ITEM,
    # 트랜잭션
    POS_CLOSING_ENTRY,
    SUBSCRIPTION,
    SUBSCRIPTION_INVOICE,
    RECURRING_INVOICE,
    SALES_COMMISSION,
    DROP_SHIP_ORDER,
    MARKETPLACE_ORDER,
    RENTAL_ORDER,
    RENTAL_RETURN,
    RETURN_MERCHANDISE_AUTHORIZATION,
    EXPORT_DECLARATION,
]
