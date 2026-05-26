"""Rental 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

5개 엔티티를 EntityMeta로 선언한다.
- 마스터: rental_items, rental_maintenances
- 트랜잭션: rental_orders, rental_returns, rental_invoices
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.rental_invoice import RentalInvoice, RentalInvoiceCreate, RentalInvoiceUpdate
from .models.rental_item import RentalItem, RentalItemCreate, RentalItemUpdate
from .models.rental_maintenance import (
    RentalMaintenance,
    RentalMaintenanceCreate,
    RentalMaintenanceUpdate,
)
from .models.rental_order import RentalOrder, RentalOrderCreate, RentalOrderUpdate
from .models.rental_return import RentalReturn, RentalReturnCreate, RentalReturnUpdate

# --- 마스터 데이터 ---

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

RENTAL_MAINTENANCE = EntityMeta(
    collection="rental_maintenances",
    prefix="RNMNT",
    api_path="/api/v1/rental-maintenances",
    tag="렌탈 유지보수",
    resource="rental_maintenance",
    model=RentalMaintenance,
    create_schema=RentalMaintenanceCreate,
    update_schema=RentalMaintenanceUpdate,
    archetype="master",
    not_found_message="렌탈 유지보수를 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

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

RENTAL_INVOICE = EntityMeta(
    collection="rental_invoices",
    prefix="RNINV",
    api_path="/api/v1/rental-invoices",
    tag="렌탈 청구서",
    resource="rental_invoice",
    model=RentalInvoice,
    create_schema=RentalInvoiceCreate,
    update_schema=RentalInvoiceUpdate,
    archetype="transaction",
    not_found_message="렌탈 청구서를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    RENTAL_ITEM,
    RENTAL_MAINTENANCE,
    # 트랜잭션
    RENTAL_ORDER,
    RENTAL_RETURN,
    RENTAL_INVOICE,
]
