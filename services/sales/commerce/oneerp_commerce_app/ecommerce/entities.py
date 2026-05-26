"""전자상거래 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

ECommerceChannel, MarketplaceOrder, DropShipOrder 엔티티를 EntityMeta로 선언한다.
MarketplaceOrder의 동기화·확인 로직은 routes/에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.drop_ship_order import DropShipOrder, DropShipOrderCreate, DropShipOrderUpdate
from .models.ecommerce_channel import (
    ECommerceChannel,
    ECommerceChannelCreate,
    ECommerceChannelUpdate,
)
from .models.marketplace_order import (
    MarketplaceOrder,
    MarketplaceOrderCreate,
    MarketplaceOrderUpdate,
)

ENTITY_METAS: list[EntityMeta] = [
    # 마스터 데이터
    EntityMeta(
        collection="ecommerce_channels",
        prefix="ECH",
        api_path="/api/v1/ecommerce/channels",
        tag="전자상거래 채널",
        resource="ecommerce_channel",
        model=ECommerceChannel,
        create_schema=ECommerceChannelCreate,
        update_schema=ECommerceChannelUpdate,
        archetype="master",
        not_found_message="전자상거래 채널을 찾을 수 없습니다",
    ),
    # 트랜잭션 문서
    EntityMeta(
        collection="marketplace_orders",
        prefix="MPO",
        api_path="/api/v1/ecommerce/marketplace-orders",
        tag="마켓플레이스 주문",
        resource="marketplace_order",
        model=MarketplaceOrder,
        create_schema=MarketplaceOrderCreate,
        update_schema=MarketplaceOrderUpdate,
        archetype="transaction",
        not_found_message="마켓플레이스 주문을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="drop_ship_orders",
        prefix="DSO",
        api_path="/api/v1/ecommerce/drop-ship-orders",
        tag="드롭쉬핑 주문",
        resource="drop_ship_order",
        model=DropShipOrder,
        create_schema=DropShipOrderCreate,
        update_schema=DropShipOrderUpdate,
        archetype="transaction",
        not_found_message="드롭쉬핑 주문을 찾을 수 없습니다",
    ),
]
