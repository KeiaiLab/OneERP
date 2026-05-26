"""Expenses 서비스 엔티티 메타 선언.

5개 엔티티를 EntityMeta로 선언한다.
모든 엔티티는 커스텀 로직(승인/반려, 법인카드 거래 등)이 있어
routes/ 디렉토리에서 직접 관리하므로, ENTITY_METAS에는 포함하지 않는다.
(ENTITY_METAS에 등록하면 create_service_app이 자동 CRUD를 생성하여
extra_routers와 동일 경로에 이중 등록된다.)
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.corporate_card import (
    CorporateCard,
    CorporateCardCreate,
    CorporateCardUpdate,
)
from .models.corporate_card_transaction import (
    CorporateCardTransaction,
    CorporateCardTransactionCreate,
    CorporateCardTransactionUpdate,
)
from .models.expense_claim import (
    ExpenseClaim,
    ExpenseClaimCreate,
    ExpenseClaimUpdate,
)
from .models.expense_type import (
    ExpenseType,
    ExpenseTypeCreate,
    ExpenseTypeUpdate,
)
from .models.travel_request import (
    TravelRequest,
    TravelRequestCreate,
    TravelRequestUpdate,
)

# --- 마스터 데이터 ---

EXPENSE_TYPE = EntityMeta(
    collection="expense_types",
    prefix="EXT",
    api_path="/api/v1/expense-types",
    tag="경비유형",
    resource="expense_type",
    model=ExpenseType,
    create_schema=ExpenseTypeCreate,
    update_schema=ExpenseTypeUpdate,
    archetype="master",
    not_found_message="경비유형을 찾을 수 없습니다",
)

CORPORATE_CARD = EntityMeta(
    collection="corporate_cards",
    prefix="CC",
    api_path="/api/v1/corporate-cards",
    tag="법인카드",
    resource="corporate_card",
    model=CorporateCard,
    create_schema=CorporateCardCreate,
    update_schema=CorporateCardUpdate,
    archetype="master",
    not_found_message="법인카드를 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

EXPENSE_CLAIM = EntityMeta(
    collection="expense_claims",
    prefix="EXP",
    api_path="/api/v1/expense-claims",
    tag="경비청구",
    resource="expense_claim",
    model=ExpenseClaim,
    create_schema=ExpenseClaimCreate,
    update_schema=ExpenseClaimUpdate,
    archetype="transaction",
    not_found_message="경비청구를 찾을 수 없습니다",
)

CORPORATE_CARD_TRANSACTION = EntityMeta(
    collection="corporate_card_transactions",
    prefix="CCT",
    api_path="/api/v1/corporate-card-transactions",
    tag="법인카드거래",
    resource="corporate_card_transaction",
    model=CorporateCardTransaction,
    create_schema=CorporateCardTransactionCreate,
    update_schema=CorporateCardTransactionUpdate,
    archetype="transaction",
    not_found_message="법인카드거래를 찾을 수 없습니다",
)

TRAVEL_REQUEST = EntityMeta(
    collection="travel_requests",
    prefix="TR",
    api_path="/api/v1/travel-requests",
    tag="출장신청",
    resource="travel_request",
    model=TravelRequest,
    create_schema=TravelRequestCreate,
    update_schema=TravelRequestUpdate,
    archetype="transaction",
    not_found_message="출장신청을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
# — 모든 엔티티가 커스텀 라우터(extra_routers)를 사용하므로
#   자동 CRUD 생성 대상은 없다.
ENTITY_METAS: list[EntityMeta] = []
