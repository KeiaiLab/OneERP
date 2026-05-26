# 이벤트 시스템 가이드 (Event System Guide)

OneERP의 서비스 간 비동기 통신 (async inter-service communication)을 위한 이벤트 시스템을 설명한다.
This guide explains the event system for async inter-service communication in OneERP.

---

## Outbox 패턴 (Outbox Pattern)

OneERP는 Outbox 패턴을 사용하여 이벤트 발행의 신뢰성 (reliability)을 보장한다.

1. 비즈니스 트랜잭션과 이벤트 저장을 동일 DB 트랜잭션으로 처리 (Business transaction and event storage in the same DB transaction)
2. 별도 폴러 (poller)가 Outbox 컬렉션에서 미발행 이벤트를 읽어 NATS로 발행 (Poller reads unpublished events from Outbox collection and publishes to NATS)
3. 발행 완료 후 이벤트를 "발행 완료" 상태로 마킹 (Mark as "published" after delivery)

```
[서비스 (Service)] ──write──→ [FerretDB: outbox 컬렉션]
                                        │
                               [Outbox Poller] ──publish──→ [NATS JetStream]
                                                                    │
                                                           [구독 서비스 (Subscriber)]
```

이 패턴은 **최소 1회 전달 (at-least-once delivery)** 을 보장하므로, 구독자 (subscriber)는 멱등성 (idempotency)을 유지해야 한다.

---

## EventType 추가 (Adding EventType)

새 도메인 이벤트 (domain event)를 추가할 때는 `packages/core/oneerp_core/events.py`의 `EventType` enum에 등록한다.

```python
class EventType(str, Enum):
    """도메인 이벤트 타입 (Domain event types)."""

    # Selling 도메인
    SALES_ORDER_SUBMITTED = "sales_order.submitted"
    SALES_ORDER_CANCELLED = "sales_order.cancelled"

    # 새 이벤트 추가 (Add new event)
    NEW_ENTITY_SUBMITTED = "new_entity.submitted"
```

### 이벤트 이름 규칙 (Event Naming Convention)

```
{엔티티_snake_case}.{동작_과거형}
예시 (Examples):
  sales_order.submitted
  expense_claim.approved
  stock.reserved
  employee.created
```

---

## EventHandlerRegistry 사용법 (Using EventHandlerRegistry)

각 서비스는 `app/events.py`에 이벤트 핸들러 레지스트리 (event handler registry)를 정의한다.

### 핸들러 등록 (Registering Handlers)

```python
"""Stock 서비스 이벤트 핸들러 (Stock service event handlers)."""

from __future__ import annotations

import logging

from oneerp_core.events import EventHandlerRegistry, EventType
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

registry = EventHandlerRegistry()


@registry.on(EventType.SALES_ORDER_SUBMITTED)
def 판매주문_제출시_재고예약(event_data: dict) -> None:
    """판매주문 제출 시 해당 아이템의 재고를 예약한다.
    Reserve stock for items when a sales order is submitted.
    """
    doc_id = event_data["doc_id"]
    tenant_id = event_data["tenant_id"]
    items = event_data.get("data", {}).get("items", [])

    repo = Repository("stock_reservations", tenant_id=tenant_id)
    for item in items:
        repo.insert({
            "source_doc": doc_id,
            "item_code": item["item_code"],
            "qty": item["qty"],
            "warehouse": item["warehouse"],
            "tenant_id": tenant_id,
        })
    logger.info("재고 예약 완료: source=%s, items=%d", doc_id, len(items))


@registry.on(EventType.SALES_ORDER_CANCELLED)
def 판매주문_취소시_예약해제(event_data: dict) -> None:
    """판매주문 취소 시 재고 예약을 해제한다.
    Release stock reservation when a sales order is cancelled.
    """
    doc_id = event_data["doc_id"]
    tenant_id = event_data["tenant_id"]

    repo = Repository("stock_reservations", tenant_id=tenant_id)
    # source_doc 기준으로 예약 삭제 (Delete reservations by source_doc)
    reservations = repo.find_many(filter={"source_doc": doc_id})
    for r in reservations:
        repo.delete_by_id(r["_id"])
    logger.info("재고 예약 해제: source=%s", doc_id)
```

### main.py에 등록 (Register in main.py)

```python
from .events import registry as event_registry

app = create_service_app(
    service_name="stock",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
)
```

---

## 이벤트 발행 (Publishing Events)

비즈니스 로직에서 이벤트를 발행한다.

```python
from oneerp_core.events import DomainEvent, EventType, publish_event


def submit_sales_order(doc_id: str, tenant_id: str, user_sub: str, items: list) -> None:
    """판매주문을 제출하고 이벤트를 발행한다.
    Submit a sales order and publish an event.
    """
    # ... 비즈니스 로직 (business logic) ...

    event = DomainEvent(
        event_type=EventType.SALES_ORDER_SUBMITTED,
        doc_id=doc_id,
        tenant_id=tenant_id,
        data={"items": items, "total_amount": total},
        triggered_by=user_sub,
    )
    publish_event(event)
```

### EventEnvelope 구조 (EventEnvelope Structure)

발행된 이벤트는 `EventEnvelope`로 감싸진다:

```json
{
  "event_id": "uuid-...",
  "event": {
    "event_type": "sales_order.submitted",
    "doc_id": "SO-2026-00001",
    "tenant_id": "tenant-001",
    "data": {"items": [...], "total_amount": 100000},
    "triggered_by": "user-001"
  },
  "source_service": "selling",
  "timestamp": "2026-03-23T10:00:00Z",
  "schema_version": 1
}
```

---

## 멱등성 보장 (Idempotency)

Outbox 패턴은 **최소 1회 전달 (at-least-once delivery)** 을 보장하므로, 동일 이벤트가 중복 전달될 수 있다.
이벤트 핸들러는 반드시 멱등성 (idempotency)을 유지해야 한다.

### 멱등성 구현 전략 (Idempotency Strategies)

#### 1. event_id 기반 중복 검사 (Dedup by event_id)

```python
@registry.on(EventType.SALES_ORDER_SUBMITTED)
def 재고예약_멱등(event_data: dict) -> None:
    """event_id 기반으로 중복 처리를 방지한다.
    Prevent duplicate processing based on event_id.
    """
    event_id = event_data["event_id"]
    repo = Repository("processed_events", tenant_id=event_data["tenant_id"])

    # 이미 처리된 이벤트인지 확인 (Check if already processed)
    existing = repo.find_by_id(event_id)
    if existing:
        logger.info("이미 처리된 이벤트 무시: %s", event_id)
        return

    # 실제 처리 (Actual processing)
    _do_reserve_stock(event_data)

    # 처리 완료 기록 (Record as processed)
    repo.insert({"_id": event_id, "processed_at": datetime.utcnow()})
```

#### 2. Upsert 사용 (Using Upsert)

동일 데이터를 다시 써도 결과가 같도록 upsert를 사용한다.
Use upsert so re-writing the same data yields the same result.

```python
# 삽입 대신 upsert (Upsert instead of insert)
repo.upsert(
    filter={"source_doc": doc_id, "item_code": item_code},
    update={"$set": {"qty": qty, "warehouse": warehouse}},
)
```

#### 3. 상태 기반 검사 (State-based Check)

처리 전 현재 상태를 확인하여 이미 처리된 경우 건너뛴다.

```python
doc = repo.find_by_id(doc_id)
if doc.get("docstatus") == 1:
    # 이미 제출됨 --- 중복 이벤트 무시 (Already submitted — skip duplicate)
    return
```

---

## NATS JetStream 설정 (NATS Configuration)

### 환경변수 (Environment Variables)

| 변수 (Variable) | 기본값 (Default) | 설명 (Description) |
|------|--------|------|
| `ONEERP_NATS_URL` | `nats://localhost:4222` | NATS 서버 URL (NATS server URL) |
| `ONEERP_NATS_STREAM` | `oneerp-events` | JetStream 스트림명 (JetStream stream name) |

### 스트림 구성 (Stream Configuration)

```
스트림명 (Stream): oneerp-events
주제 패턴 (Subject pattern): oneerp.events.{event_type}
보존 정책 (Retention): WorkQueue (소비 후 삭제 / delete after consumption)
복제본 수 (Replicas): 3 (운영 환경 / production)
최대 전달 횟수 (Max deliver): 5
```

### 구독 설정 (Subscription Configuration)

각 서비스는 자체 consumer group으로 이벤트를 구독한다.
Each service subscribes to events via its own consumer group.

```
Consumer Group: {service_name}-consumer
Durable Name: {service_name}-{event_type}
Ack Policy: Explicit (명시적 확인)
Ack Wait: 30s
```

---

## 이벤트 흐름 예시 (Event Flow Example — Order-to-Cash)

```
[Selling]                    [Stock]                [Accounting]
    │                          │                        │
    ├─ sales_order.submitted ─→│ 재고 예약 (Reserve)    │
    │                          ├─ stock.reserved ──────→│
    │                          │                        │
    ├─ delivery_note.submitted→│ 재고 차감 (Deduct)     │
    │                          ├─ stock.delivered ─────→│ 매출 분개 (Revenue JE)
    │                          │                        │
    ├─ sales_invoice.submitted─────────────────────────→│ AR 분개 (AR JE)
    │                          │                        │
    │                          │         payment_entry ←│ 수금 처리 (Payment)
    │← AR 차감 (AR Reduction) ←────────────────────────←│
```

---

## 이벤트 테스트 (Testing Events)

이벤트 핸들러는 단위 테스트에서 직접 함수를 호출하여 테스트한다.

```python
from unittest.mock import patch, MagicMock
from app.events import 판매주문_제출시_재고예약


@patch("app.events.Repository")
def test_판매주문_제출시_재고예약_정상(mock_repo_cls: MagicMock) -> None:
    """판매주문 이벤트가 도착하면 재고 예약 문서를 생성한다.
    Stock reservation document is created when sales order event arrives.
    """
    repo = MagicMock()
    mock_repo_cls.return_value = repo

    event_data = {
        "doc_id": "SO-001",
        "tenant_id": "t-001",
        "data": {
            "items": [
                {"item_code": "ITEM-001", "qty": 10, "warehouse": "WH-001"},
            ],
        },
    }
    판매주문_제출시_재고예약(event_data)

    repo.insert.assert_called_once()
    call_args = repo.insert.call_args[0][0]
    assert call_args["item_code"] == "ITEM-001"
    assert call_args["qty"] == 10
```
