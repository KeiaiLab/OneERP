# 비즈니스 로직 추가 방법 (How to Add Business Logic)

EntityMeta 자동 CRUD 외에 커스텀 비즈니스 로직 (custom business logic)을 추가하는 방법을 설명한다.
This guide explains how to add custom business logic beyond EntityMeta auto-generated CRUD.

---

## 서비스 클래스 패턴 (Service Class Pattern)

비즈니스 로직은 `services/{서비스명}/app/services/` 디렉토리에 서비스 클래스로 구현한다.
라우터 (router)는 HTTP 요청/응답만 처리하고, 비즈니스 규칙은 서비스 클래스에 위임한다.
Routers handle HTTP request/response only; business rules are delegated to service classes.

```python
"""경비청구 서비스 (Expense Claim Service)."""

from __future__ import annotations

import logging

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class ExpenseClaimService:
    """경비청구 비즈니스 로직을 캡슐화한다.
    Encapsulates expense claim business logic.
    """

    def __init__(self, tenant_id: str) -> None:
        self._repo = Repository("expense_claims", tenant_id=tenant_id)
        self._tenant_id = tenant_id

    def submit(self, doc_id: str, user_sub: str) -> dict:
        """경비청구를 제출한다 (Submit expense claim).

        Draft → Submitted 상태 전이 (state transition).
        비즈니스 규칙 (business rules):
        - 금액이 0보다 커야 한다 (Amount must be > 0)
        - 증빙이 첨부되어야 한다 (Receipts must be attached)
        """
        doc = self._repo.find_by_id(doc_id)
        if not doc:
            msg = "경비청구를 찾을 수 없습니다"
            raise ValueError(msg)
        if doc.get("docstatus", 0) != 0:
            msg = "초안 상태에서만 제출할 수 있습니다"
            raise ValueError(msg)
        if doc.get("total_amount", 0) <= 0:
            msg = "총 금액이 0보다 커야 합니다"
            raise ValueError(msg)

        self._repo.update_by_id(doc_id, {
            "docstatus": 1,
            "updated_by": user_sub,
        })
        logger.info("경비청구 제출 완료: doc_id=%s", doc_id)
        return {**doc, "docstatus": 1}

    def approve(self, doc_id: str, approver_sub: str) -> dict:
        """경비청구를 승인한다 (Approve expense claim)."""
        doc = self._repo.find_by_id(doc_id)
        if not doc:
            msg = "경비청구를 찾을 수 없습니다"
            raise ValueError(msg)
        if doc.get("docstatus", 0) != 1:
            msg = "제출된 상태에서만 승인할 수 있습니다"
            raise ValueError(msg)

        self._repo.update_by_id(doc_id, {
            "approval_status": "approved",
            "approved_by": approver_sub,
        })
        logger.info("경비청구 승인 완료: doc_id=%s, approver=%s", doc_id, approver_sub)
        return {**doc, "approval_status": "approved"}
```

라우터에서 서비스 클래스를 사용하는 방법 (Using service class in router):

```python
@router.post("/{doc_id}/submit")
def 경비청구_제출(doc_id: str, user: CurrentUserDep) -> dict:
    """경비청구를 제출한다."""
    svc = ExpenseClaimService(tenant_id=user.tenant_id)
    try:
        return svc.submit(doc_id, user.sub)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
```

---

## Repository 사용법 (Using Repository)

`Repository`는 FerretDB 컬렉션 (collection)에 대한 제네릭 CRUD 추상화 (generic CRUD abstraction)를 제공한다.
모든 쿼리에 `tenant_id`가 자동으로 적용된다 (auto-applied to all queries).

### 기본 CRUD 메서드 (Basic CRUD Methods)

```python
from oneerp_core.repository import Repository

repo = Repository("items", tenant_id="tenant-001")

# 삽입 (Insert)
repo.insert(item_doc)

# ID로 조회 (Find by ID)
doc = repo.find_by_id("ITEM-2026-00001")

# 목록 조회 (Find many)
docs = repo.find_many(
    filter={"item_group": "원자재"},   # 추가 필터 (additional filter)
    skip=0,
    limit=20,
    sort=[("created_at", -1)],
)

# 건수 조회 (Count)
count = repo.count(filter={"item_group": "원자재"})

# ID로 수정 (Update by ID)
repo.update_by_id("ITEM-2026-00001", {"stock_uom": "kg"})

# ID로 삭제 (Delete by ID)
repo.delete_by_id("ITEM-2026-00001")
```

### 주의사항 (Important Notes)

- `tenant_id`를 직접 필터에 추가하지 않는다 --- Repository가 자동 처리한다.
  Do not add `tenant_id` to filters manually --- Repository handles it automatically.
- `date` 타입은 FerretDB(BSON) 저장 시 자동으로 `datetime`으로 변환된다.
  `date` types are auto-converted to `datetime` for FerretDB(BSON) storage.

---

## 이벤트 핸들러 작성법 (Writing Event Handlers)

서비스 간 비동기 통신 (async inter-service communication)은 도메인 이벤트 (domain events)로 처리된다.

### 이벤트 발행 (Publishing Events)

```python
from oneerp_core.events import DomainEvent, EventType, publish_event

event = DomainEvent(
    event_type=EventType.EXPENSE_CLAIM_SUBMITTED,
    doc_id=doc_id,
    tenant_id=tenant_id,
    data={"total_amount": total_amount},
    triggered_by=user_sub,
)
publish_event(event)
```

### 이벤트 구독 (Subscribing to Events)

`services/{서비스명}/app/events.py`에 이벤트 핸들러를 등록한다.

```python
"""이벤트 핸들러 등록 (Event handler registration)."""

from __future__ import annotations

from oneerp_core.events import EventHandlerRegistry, EventType

registry = EventHandlerRegistry()


@registry.on(EventType.SALES_ORDER_SUBMITTED)
def 판매주문_제출_처리(event_data: dict) -> None:
    """판매주문 제출 시 재고 예약을 수행한다.
    Reserve stock when a sales order is submitted.
    """
    doc_id = event_data["doc_id"]
    tenant_id = event_data["tenant_id"]
    # 재고 예약 로직 (Stock reservation logic)
    ...
```

`main.py`에서 `event_registry`를 전달한다 (Pass to `main.py`):

```python
from .events import registry as event_registry

app = create_service_app(
    service_name="stock",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
)
```

---

## 단위 테스트 작성법 (Writing Unit Tests)

### 기본 패턴 (Basic Pattern)

`unittest.mock.patch`로 외부 의존성 (external dependencies)을 모킹한다.
단위 테스트 (unit tests)에서는 실제 DB 연결을 사용하지 않는다.
Unit tests should not use real DB connections.

```python
"""경비청구 제출 테스트 (Expense claim submit tests)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.expense_service import ExpenseClaimService


@patch("app.services.expense_service.Repository")
def test_경비청구_제출_정상(mock_repo_cls: MagicMock) -> None:
    """초안 경비청구를 제출하면 docstatus가 1이 된다.
    Submitting a draft expense claim sets docstatus to 1.
    """
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "EXP-001",
        "docstatus": 0,
        "total_amount": 50000,
    }
    mock_repo_cls.return_value = repo

    svc = ExpenseClaimService(tenant_id="t-001")
    result = svc.submit("EXP-001", "user-001")

    assert result["docstatus"] == 1
    repo.update_by_id.assert_called_once()


@patch("app.services.expense_service.Repository")
def test_경비청구_제출_금액_0_오류(mock_repo_cls: MagicMock) -> None:
    """총 금액이 0인 경비청구는 제출할 수 없다.
    Expense claim with 0 total cannot be submitted.
    """
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "EXP-002",
        "docstatus": 0,
        "total_amount": 0,
    }
    mock_repo_cls.return_value = repo

    svc = ExpenseClaimService(tenant_id="t-001")
    with pytest.raises(ValueError, match="총 금액"):
        svc.submit("EXP-002", "user-001")
```

### 라우터 테스트 패턴 (Router Test Pattern)

`FastAPI TestClient`로 HTTP 레벨 테스트를 작성한다.

```python
from unittest.mock import MagicMock, patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("app.routes.examples._get_repo")
@patch("app.routes.examples.generate_name", return_value="EXM-2026-00001")
def test_예시_생성_201(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/examples -- 201 반환을 확인한다."""
    mock_repo.return_value = MagicMock()
    response = client.post("/api/v1/examples", json={"name": "테스트"})
    assert response.status_code == 201
```

### 테스트 실행 (Running Tests)

```bash
# 서비스별 단위 테스트 (Per-service unit tests)
uv run --directory services/{서비스명} pytest tests/ -m "not integration and not e2e" -q

# 통합 테스트 (Integration tests — requires running FerretDB)
uv run --directory services/{서비스명} pytest tests/ -m integration -q
```
