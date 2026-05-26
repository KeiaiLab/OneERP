"""Buying 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

5개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 10개 엔티티(purchase_orders, purchase_invoices, purchase_receipts,
material_requests, supplier_quotations, purchase_returns, request_for_quotations,
landed_cost_vouchers, purchase_analytics)는 routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.buyer_approval_matrix import (
    BuyerApprovalMatrix,
    BuyerApprovalMatrixCreate,
    BuyerApprovalMatrixUpdate,
)
from .models.import_declaration import (
    ImportDeclaration,
    ImportDeclarationCreate,
    ImportDeclarationUpdate,
)
from .models.purchase_pricing_rule import (
    PurchasePricingRule,
    PurchasePricingRuleCreate,
    PurchasePricingRuleUpdate,
)
from .models.supplier_group import SupplierGroup, SupplierGroupCreate, SupplierGroupUpdate
from .models.supplier_scorecard import (
    SupplierScorecard,
    SupplierScorecardCreate,
    SupplierScorecardUpdate,
)

# --- 마스터 데이터 ---

SUPPLIER_GROUP = EntityMeta(
    collection="supplier_groups",
    prefix="SGR",
    api_path="/api/v1/supplier-groups",
    tag="공급업체그룹",
    resource="supplier_group",
    model=SupplierGroup,
    create_schema=SupplierGroupCreate,
    update_schema=SupplierGroupUpdate,
    archetype="master",
    not_found_message="공급업체그룹을 찾을 수 없습니다",
)

SUPPLIER_SCORECARD = EntityMeta(
    collection="supplier_scorecards",
    prefix="SSC",
    api_path="/api/v1/supplier-scorecards",
    tag="공급업체평가",
    resource="supplier_scorecard",
    model=SupplierScorecard,
    create_schema=SupplierScorecardCreate,
    update_schema=SupplierScorecardUpdate,
    archetype="master",
    not_found_message="공급업체평가를 찾을 수 없습니다",
)

BUYER_APPROVAL_MATRIX = EntityMeta(
    collection="buyer_approval_matrices",
    prefix="BAM",
    api_path="/api/v1/buyer-approval-matrices",
    tag="구매승인매트릭스",
    resource="buyer_approval_matrix",
    model=BuyerApprovalMatrix,
    create_schema=BuyerApprovalMatrixCreate,
    update_schema=BuyerApprovalMatrixUpdate,
    archetype="master",
    not_found_message="구매승인매트릭스를 찾을 수 없습니다",
)

PURCHASE_PRICING_RULE = EntityMeta(
    collection="purchase_pricing_rules",
    prefix="PPRC",
    api_path="/api/v1/purchase-pricing-rules",
    tag="구매가격규칙",
    resource="purchase_pricing_rule",
    model=PurchasePricingRule,
    create_schema=PurchasePricingRuleCreate,
    update_schema=PurchasePricingRuleUpdate,
    archetype="master",
    not_found_message="구매 가격규칙을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

IMPORT_DECLARATION = EntityMeta(
    collection="import_declarations",
    prefix="IMPD",
    api_path="/api/v1/import-declarations",
    tag="수입 신고",
    resource="import_declaration",
    model=ImportDeclaration,
    create_schema=ImportDeclarationCreate,
    update_schema=ImportDeclarationUpdate,
    archetype="transaction",
    not_found_message="수입 신고를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
# 참고: Supplier, PurchaseAnalytics는 커스텀 라우트에서 관리
ENTITY_METAS = [
    SUPPLIER_GROUP,
    SUPPLIER_SCORECARD,
    BUYER_APPROVAL_MATRIX,
    PURCHASE_PRICING_RULE,
    IMPORT_DECLARATION,
]
