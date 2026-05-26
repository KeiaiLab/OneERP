# OTC Boundary Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OTC vertical slice(selling + stock + accounting)에서 `route → service → repository` 경계 원칙을 실제 적용하고, `check_layer_boundaries.py`의 glob 불일치를 복구해 아키텍처 회귀 감지를 복원한다.

**Architecture:** 기존 `oneerp_{name}_app/` 구조 유지. 각 도메인에 `dto.py`를 신설해 Create/Update/Request/Response를 격리하고, service 레이어를 완성해 route는 service만 호출하도록 전환한다. `tests/e2e/test_order_to_cash_flow.py`를 회귀 감지 안전망으로 사용.

**Tech Stack:** Python 3.14, Pydantic v2, FastAPI 0.115+, pytest, uv workspace, ruff 0.15

---

## Phase 1. 체커 복구 + baseline 재측정

### Task 1.1: glob 패턴을 실제 구조에 맞게 수정

**Files:**
- Modify: `scripts/dev/check_layer_boundaries.py` (27-29행)

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_check_layer_boundaries.py` 하단에 추가:

```python
def test_glob이_oneerp_app_구조를_인식한다() -> None:
    """현재 서비스 구조는 services/<도메인>/<서비스>/oneerp_<이름>_app/... 이다."""
    import importlib.util
    module_path = ROOT / "scripts" / "dev" / "check_layer_boundaries.py"
    spec = importlib.util.spec_from_file_location("cblm", module_path)
    assert spec and spec.loader
    cblm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cblm)

    assert "oneerp_" in cblm.ROUTES_GLOB, (
        f"ROUTES_GLOB가 oneerp_*_app 구조를 반영해야 함: {cblm.ROUTES_GLOB}"
    )
    assert "oneerp_" in cblm.MODELS_GLOB, (
        f"MODELS_GLOB가 oneerp_*_app 구조를 반영해야 함: {cblm.MODELS_GLOB}"
    )
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_glob이_oneerp_app_구조를_인식한다 -v
```
Expected: FAIL — 현재 `app/` 경로를 사용하므로 `oneerp_` 문자열 부재.

- [ ] **Step 3: 최소 구현 — glob 패턴 수정**

`scripts/dev/check_layer_boundaries.py` 27-29행을 다음으로 교체:

```python
ROUTES_GLOB = "services/*/*/oneerp_*_app/routes/*.py"
MODELS_GLOB = "services/*/*/oneerp_*_app/models/*.py"
PLANE_GLOB = "planes/**/*.py"
```

- [ ] **Step 4: 패스 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py -v
```
Expected: PASS (기존 2개 + 신규 1개 = 3 tests)

- [ ] **Step 5: 커밋**

```bash
git add scripts/dev/check_layer_boundaries.py tests/unit/test_check_layer_boundaries.py
git commit -m "fix(arch): check_layer_boundaries glob을 oneerp_*_app 구조에 맞춤"
```

---

### Task 1.2: 실제 위반 수 측정 + 새 baseline 기록

**Files:**
- Modify: `.arch-baseline.json`

- [ ] **Step 1: 새 현황 측정**

```bash
uv run python scripts/dev/check_layer_boundaries.py
```

출력에서 각 규칙별 "N건" 숫자를 기록한다. 예상: OE002/OE004는 0이 아닌 실제 값이 출력된다.

- [ ] **Step 2: 현재 실제 값으로 baseline 업데이트**

`.arch-baseline.json`을 Step 1의 출력값으로 교체한다 (예시 — 실제 값으로 대체):

```json
{
  "OE002-route-direct-repo-instantiate": <실측값>,
  "OE002-route-import-repository": <실측값>,
  "OE004-models-define-create-dto": <실측값>,
  "OE101-plane-domain-rule-leak": 0,
  "OE201-web-contract-bypass": 0
}
```

- [ ] **Step 3: `--check` 동작 확인**

```bash
uv run python scripts/dev/check_layer_boundaries.py --check
```
Expected: `✓ baseline 대비 위반 증가 없음` 출력.

- [ ] **Step 4: 커밋**

```bash
git add .arch-baseline.json
git commit -m "chore(arch): 실제 구조 기준 baseline 재측정"
```

---

### Task 1.3: Phase 1 Smoke 회귀

**Files:**
- Test: `tests/unit/test_check_layer_boundaries.py`

- [ ] **Step 1: 전체 구조 테스트 실행**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py -v
uv run python scripts/dev/check_layer_boundaries.py --check
```
Expected: 모두 PASS, baseline 통과.

- [ ] **Step 2: 이후 phase에서 baseline을 줄여나갈 수 있는지 sanity check**

baseline 파일의 OE002/OE004 숫자가 0이 아니어야 한다 (0이면 Phase 2~4에서 감소 여지 없음).

```bash
grep -E "OE002|OE004" .arch-baseline.json
```
Expected: 3개 키 모두 양수.

- [ ] **Step 3: Phase 1 종료 (커밋 없음 — 읽기 전용 검증)**

---

## Phase 2. Selling OTC 슬라이스

### Task 2.1: selling/dto.py 신설 + sales_order Create/Update 이동

**Files:**
- Create: `services/sales/selling/oneerp_selling_app/dto.py`
- Modify: `services/sales/selling/oneerp_selling_app/models/sales_order.py`
- Modify: `services/sales/selling/oneerp_selling_app/routes/sales_orders.py` (import만 교체)

- [ ] **Step 1: 실패 테스트 작성**

`services/sales/selling/tests/unit/test_dto_boundary.py` 신설:

```python
"""OE004: Create/Update DTO는 models/가 아닌 dto.py에 존재해야 한다."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DTO_FILE = ROOT / "oneerp_selling_app" / "dto.py"
SALES_ORDER_MODEL = ROOT / "oneerp_selling_app" / "models" / "sales_order.py"


def test_sales_order_create_update_가_dto에_있다() -> None:
    assert DTO_FILE.exists(), f"{DTO_FILE}가 없음"
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class SalesOrderCreate" in text
    assert "class SalesOrderUpdate" in text


def test_sales_order_model에는_dto가_없다() -> None:
    text = SALES_ORDER_MODEL.read_text(encoding="utf-8")
    assert "class SalesOrderCreate" not in text
    assert "class SalesOrderUpdate" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest tests/unit/test_dto_boundary.py -v
```
Expected: FAIL — dto.py 없음.

- [ ] **Step 3: dto.py 생성**

`services/sales/selling/oneerp_selling_app/dto.py`:

```python
"""selling 서비스의 Create/Update/Request/Response DTO 집약.

OE004: models/는 Document(영속 상태)만, dto는 여기에 모은다.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from .models.sales_order import SalesOrderItem


class SalesOrderCreate(BaseModel):
    customer_id: str
    customer_name: str
    transaction_date: date
    delivery_date: date
    items: list[SalesOrderItem] = Field(default_factory=list)


class SalesOrderUpdate(BaseModel):
    customer_id: str | None = None
    customer_name: str | None = None
    transaction_date: date | None = None
    delivery_date: date | None = None
    items: list[SalesOrderItem] | None = None
```

- [ ] **Step 4: models/sales_order.py에서 Create/Update 제거**

`services/sales/selling/oneerp_selling_app/models/sales_order.py`의 `SalesOrderCreate`, `SalesOrderUpdate` 클래스 정의 블록을 삭제한다 (라인 25~42 근방). `SalesOrderItem`, `SalesOrder` 클래스는 유지.

- [ ] **Step 5: sales_orders route의 DTO import 교체**

`services/sales/selling/oneerp_selling_app/routes/sales_orders.py`에서:

```python
# OLD
from ..models.sales_order import SalesOrderCreate, SalesOrderUpdate, SalesOrder
# NEW
from ..dto import SalesOrderCreate, SalesOrderUpdate
from ..models.sales_order import SalesOrder
```

- [ ] **Step 6: 테스트 패스 확인**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest tests/unit/test_dto_boundary.py -v
uv run --package oneerp-selling --directory services/sales/selling pytest -q
```
Expected: 신규 2개 + 기존 모든 테스트 PASS.

- [ ] **Step 7: 커밋**

```bash
git add services/sales/selling/oneerp_selling_app/dto.py \
        services/sales/selling/oneerp_selling_app/models/sales_order.py \
        services/sales/selling/oneerp_selling_app/routes/sales_orders.py \
        services/sales/selling/tests/unit/test_dto_boundary.py
git commit -m "refactor(selling): sales_order DTO를 dto.py로 격리 (OE004)"
```

---

### Task 2.2: sales_order_service.py 신규 + route에서 Repository 직접사용 제거

**Files:**
- Create: `services/sales/selling/oneerp_selling_app/services/sales_order_service.py`
- Modify: `services/sales/selling/oneerp_selling_app/routes/sales_orders.py`

- [ ] **Step 1: 실패 테스트 작성**

`services/sales/selling/tests/unit/test_route_boundary.py` 신설:

```python
"""OE002: route는 Repository를 직접 import/인스턴스화 하지 않는다."""

from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[3] / "oneerp_selling_app" / "routes"


def test_sales_orders_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "sales_orders.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text, (
        "route는 service 계층을 거쳐야 함"
    )
    assert "Repository(" not in text, "route는 Repository를 직접 인스턴스화하지 말 것"
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest tests/unit/test_route_boundary.py -v
```
Expected: FAIL (현재 route에 Repository import + 인스턴스화 존재).

- [ ] **Step 3: sales_order_service.py 작성**

`services/sales/selling/oneerp_selling_app/services/sales_order_service.py`:

```python
"""판매주문 비즈니스 로직 — route/Repository 사이의 경계 계층."""

from __future__ import annotations

from typing import Any

from oneerp_core.repository import Repository

from ..dto import SalesOrderCreate, SalesOrderUpdate
from ..models.sales_order import SalesOrder

_COLLECTION = "sales_orders"


class SalesOrderService:
    """판매주문 유스케이스 — create/submit/update/cancel 등 명시적 동작만 노출."""

    def __init__(self, tenant_id: str) -> None:
        self._repo: Repository = Repository(_COLLECTION, tenant_id=tenant_id)

    def create(self, dto: SalesOrderCreate) -> str:
        doc = SalesOrder(**dto.model_dump())
        return self._repo.insert(doc)

    def get(self, so_id: str) -> dict[str, Any] | None:
        return self._repo.find_by_id(so_id)

    def list(self, *, limit: int = 100, **filters: Any) -> list[dict[str, Any]]:
        return self._repo.find_many(filters, limit=limit)

    def update(self, so_id: str, dto: SalesOrderUpdate) -> dict[str, Any] | None:
        patch = {k: v for k, v in dto.model_dump().items() if v is not None}
        self._repo.update_by_id(so_id, patch)
        return self._repo.find_by_id(so_id)

    def submit(self, so_id: str) -> dict[str, Any] | None:
        self._repo.submit(so_id)
        return self._repo.find_by_id(so_id)
```

- [ ] **Step 4: sales_orders route를 service로 전환**

`services/sales/selling/oneerp_selling_app/routes/sales_orders.py`에서:
- `from oneerp_core.repository import Repository` 라인 삭제
- `_get_repo(...)` 등 Repository 직접 생성 함수 삭제
- DI 패턴으로 전환:

```python
from typing import Annotated

from fastapi import Depends
from oneerp_core.auth import require_tenant  # 기존 DI 헬퍼 사용

from ..services.sales_order_service import SalesOrderService


def get_service(
    tenant_id: Annotated[str, Depends(require_tenant)],
) -> SalesOrderService:
    return SalesOrderService(tenant_id)


@router.post("")
def create_sales_order(
    body: SalesOrderCreate,
    service: Annotated[SalesOrderService, Depends(get_service)],
) -> dict[str, str]:
    so_id = service.create(body)
    return {"id": so_id}
```

주의: 기존 route의 핸들러 시그니처 (경로, 응답 스키마, status_code)는 유지한다.

- [ ] **Step 5: 테스트 패스 확인**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest -q
```
Expected: 기존 유닛 + 신규 경계 테스트 PASS.

- [ ] **Step 6: OTC E2E 회귀**

```bash
docker compose --profile infra up -d
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```
Expected: 3 passed (로그인/OTC/재로그인).

- [ ] **Step 7: 커밋**

```bash
git add services/sales/selling/oneerp_selling_app/services/sales_order_service.py \
        services/sales/selling/oneerp_selling_app/routes/sales_orders.py \
        services/sales/selling/tests/unit/test_route_boundary.py
git commit -m "refactor(selling): sales_order route → service 경계 도입 (OE002)"
```

---

### Task 2.3: delivery_note DTO 이동 + route 전환

**Files:**
- Modify: `services/sales/selling/oneerp_selling_app/dto.py` (append)
- Modify: `services/sales/selling/oneerp_selling_app/models/delivery_note.py`
- Modify: `services/sales/selling/oneerp_selling_app/routes/delivery_notes.py`
- Modify: `services/sales/selling/tests/unit/test_dto_boundary.py`
- Modify: `services/sales/selling/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 경계 테스트 확장**

`tests/unit/test_dto_boundary.py`에 추가:

```python
DELIVERY_MODEL = ROOT / "oneerp_selling_app" / "models" / "delivery_note.py"


def test_delivery_note_create_update가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class DeliveryNoteCreate" in text
    assert "class DeliveryNoteUpdate" in text


def test_delivery_note_model에는_dto가_없다() -> None:
    text = DELIVERY_MODEL.read_text(encoding="utf-8")
    assert "class DeliveryNoteCreate" not in text
    assert "class DeliveryNoteUpdate" not in text
```

`tests/unit/test_route_boundary.py`에 추가:

```python
def test_delivery_notes_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "delivery_notes.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest tests/unit/test_dto_boundary.py tests/unit/test_route_boundary.py -v
```
Expected: 신규 4개 FAIL.

- [ ] **Step 3: dto.py에 DeliveryNote 관련 DTO 추가**

`oneerp_selling_app/dto.py` 하단에:

```python
from .models.delivery_note import DeliveryNoteItem


class DeliveryNoteCreate(BaseModel):
    customer_id: str
    customer_name: str
    sales_order_id: str | None = None
    posting_date: date
    items: list[DeliveryNoteItem] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    customer_id: str | None = None
    customer_name: str | None = None
    sales_order_id: str | None = None
    posting_date: date | None = None
    items: list[DeliveryNoteItem] | None = None
```

- [ ] **Step 4: models/delivery_note.py에서 Create/Update 제거**

해당 클래스 정의 블록을 찾아 삭제 (DeliveryNoteItem과 DeliveryNote는 유지).

- [ ] **Step 5: routes/delivery_notes.py 전환**

기존 delivery_note_service.py가 이미 존재하므로 재사용. route에서:
- `from oneerp_core.repository import Repository` 삭제
- Repository 직접 사용 제거
- `DeliveryNoteService` DI 패턴으로 교체 (Task 2.2와 동일 구조)
- import를 `from ..dto import DeliveryNoteCreate, DeliveryNoteUpdate`로 변경

- [ ] **Step 6: 테스트 패스 + E2E 회귀**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest -q
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```
Expected: 전부 PASS.

- [ ] **Step 7: 커밋**

```bash
git add services/sales/selling/oneerp_selling_app/dto.py \
        services/sales/selling/oneerp_selling_app/models/delivery_note.py \
        services/sales/selling/oneerp_selling_app/routes/delivery_notes.py \
        services/sales/selling/tests/unit/test_dto_boundary.py \
        services/sales/selling/tests/unit/test_route_boundary.py
git commit -m "refactor(selling): delivery_note DTO/route 경계 정리 (OE002/OE004)"
```

---

### Task 2.4: sales_invoice DTO 이동 + route 전환

**Files:**
- Modify: `services/sales/selling/oneerp_selling_app/dto.py`
- Modify: `services/sales/selling/oneerp_selling_app/models/sales_invoice.py`
- Modify: `services/sales/selling/oneerp_selling_app/routes/sales_invoices.py`
- Modify: `services/sales/selling/tests/unit/test_dto_boundary.py`
- Modify: `services/sales/selling/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 경계 테스트 확장**

`test_dto_boundary.py`에 추가:

```python
SINV_MODEL = ROOT / "oneerp_selling_app" / "models" / "sales_invoice.py"


def test_sales_invoice_create_update가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class SalesInvoiceCreate" in text
    assert "class SalesInvoiceUpdate" in text


def test_sales_invoice_model에는_dto가_없다() -> None:
    text = SINV_MODEL.read_text(encoding="utf-8")
    assert "class SalesInvoiceCreate" not in text
    assert "class SalesInvoiceUpdate" not in text
```

`test_route_boundary.py`에 추가:

```python
def test_sales_invoices_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "sales_invoices.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest tests/unit/test_dto_boundary.py tests/unit/test_route_boundary.py -v
```
Expected: 신규 3개 FAIL.

- [ ] **Step 3: dto.py에 SalesInvoice DTO 추가**

```python
from .models.sales_invoice import SalesInvoiceItem, SalesInvoiceTax


class SalesInvoiceCreate(BaseModel):
    customer_id: str
    customer_name: str
    sales_order_id: str | None = None
    delivery_note_id: str | None = None
    posting_date: date
    due_date: date
    items: list[SalesInvoiceItem] = Field(default_factory=list)
    taxes: list[SalesInvoiceTax] = Field(default_factory=list)


class SalesInvoiceUpdate(BaseModel):
    customer_id: str | None = None
    customer_name: str | None = None
    posting_date: date | None = None
    due_date: date | None = None
    items: list[SalesInvoiceItem] | None = None
    taxes: list[SalesInvoiceTax] | None = None
```

주의: SalesInvoiceTax가 없으면 models/sales_invoice.py의 실제 타입명을 확인 후 맞춘다.

- [ ] **Step 4: models/sales_invoice.py에서 Create/Update 제거**

해당 블록 삭제 (Item, Tax, SalesInvoice 자체는 유지).

- [ ] **Step 5: routes/sales_invoices.py 전환**

기존 `sales_invoice_service.py`를 활용해 DI로 교체:
- Repository import 제거
- `SalesInvoiceService` 주입
- DTO import를 `from ..dto import SalesInvoiceCreate, SalesInvoiceUpdate`로

- [ ] **Step 6: 테스트 패스 + E2E 회귀**

```bash
uv run --package oneerp-selling --directory services/sales/selling pytest -q
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```
Expected: 전부 PASS.

- [ ] **Step 7: 커밋**

```bash
git add services/sales/selling/oneerp_selling_app/dto.py \
        services/sales/selling/oneerp_selling_app/models/sales_invoice.py \
        services/sales/selling/oneerp_selling_app/routes/sales_invoices.py \
        services/sales/selling/tests/unit/test_dto_boundary.py \
        services/sales/selling/tests/unit/test_route_boundary.py
git commit -m "refactor(selling): sales_invoice DTO/route 경계 정리 (OE002/OE004)"
```

---

## Phase 3. Stock OTC 슬라이스

### Task 3.1: stock/dto.py + items DTO/route 전환

**Files:**
- Create: `services/scm/stock/oneerp_stock_app/dto.py`
- Modify: `services/scm/stock/oneerp_stock_app/models/item.py`
- Modify: `services/scm/stock/oneerp_stock_app/routes/items.py`
- Create: `services/scm/stock/tests/unit/test_dto_boundary.py`
- Create: `services/scm/stock/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 실패 테스트 작성**

`services/scm/stock/tests/unit/test_dto_boundary.py`:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DTO_FILE = ROOT / "oneerp_stock_app" / "dto.py"
ITEM_MODEL = ROOT / "oneerp_stock_app" / "models" / "item.py"


def test_item_create_update가_dto에_있다() -> None:
    assert DTO_FILE.exists()
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class ItemCreate" in text
    assert "class ItemUpdate" in text


def test_item_model에는_dto가_없다() -> None:
    text = ITEM_MODEL.read_text(encoding="utf-8")
    assert "class ItemCreate" not in text
    assert "class ItemUpdate" not in text
```

`services/scm/stock/tests/unit/test_route_boundary.py`:

```python
from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[3] / "oneerp_stock_app" / "routes"


def test_items_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "items.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-stock --directory services/scm/stock pytest tests/unit/test_dto_boundary.py tests/unit/test_route_boundary.py -v
```
Expected: FAIL.

- [ ] **Step 3: stock/dto.py 신설 + Item DTO 이동**

`services/scm/stock/oneerp_stock_app/dto.py`:

```python
"""stock 서비스 DTO 집약 (OE004)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    item_name: str
    item_group: str
    stock_uom: str
    is_stock_item: bool = True
    item_code: str | None = None


class ItemUpdate(BaseModel):
    item_name: str | None = None
    item_group: str | None = None
    stock_uom: str | None = None
    is_stock_item: bool | None = None
```

(실제 필드는 `models/item.py`의 기존 ItemCreate/ItemUpdate 구조를 그대로 이식)

- [ ] **Step 4: models/item.py에서 Create/Update 제거**

`Item`(Document) 클래스는 유지, Create/Update 블록만 제거.

- [ ] **Step 5: items_service 존재 확인 + 없으면 생성**

```bash
ls services/scm/stock/oneerp_stock_app/services/ | grep item
```

있으면 재사용, 없으면 `services/item_service.py`를 Task 2.2 `SalesOrderService` 패턴으로 작성 (collection 이름 `items`, create/get/list/update/submit 메서드).

- [ ] **Step 6: routes/items.py 전환**

- Repository import 제거
- `ItemService` 주입 (DI)
- DTO import를 `from ..dto import ItemCreate, ItemUpdate`로

- [ ] **Step 7: 테스트 + E2E 회귀**

```bash
uv run --package oneerp-stock --directory services/scm/stock pytest -q
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```
Expected: 전부 PASS.

- [ ] **Step 8: 커밋**

```bash
git add services/scm/stock/oneerp_stock_app/dto.py \
        services/scm/stock/oneerp_stock_app/models/item.py \
        services/scm/stock/oneerp_stock_app/routes/items.py \
        services/scm/stock/oneerp_stock_app/services/ \
        services/scm/stock/tests/unit/
git commit -m "refactor(stock): item DTO/route 경계 도입 (OE002/OE004)"
```

---

### Task 3.2: purchase_receipts DTO/route 전환

**Files:**
- Modify: `services/scm/stock/oneerp_stock_app/dto.py` (append)
- Modify: `services/scm/stock/oneerp_stock_app/models/purchase_receipt.py`
- Modify: `services/scm/stock/oneerp_stock_app/routes/purchase_receipts.py`
- Modify: `services/scm/stock/tests/unit/test_dto_boundary.py`
- Modify: `services/scm/stock/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 경계 테스트 확장**

`test_dto_boundary.py`에 추가:

```python
PR_MODEL = ROOT / "oneerp_stock_app" / "models" / "purchase_receipt.py"


def test_purchase_receipt_create_update가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class PurchaseReceiptCreate" in text
    assert "class PurchaseReceiptUpdate" in text


def test_purchase_receipt_model에는_dto가_없다() -> None:
    text = PR_MODEL.read_text(encoding="utf-8")
    assert "class PurchaseReceiptCreate" not in text
    assert "class PurchaseReceiptUpdate" not in text
```

`test_route_boundary.py`에 추가:

```python
def test_purchase_receipts_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "purchase_receipts.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-stock --directory services/scm/stock pytest tests/unit/test_dto_boundary.py tests/unit/test_route_boundary.py -v
```

- [ ] **Step 3: dto.py에 PurchaseReceipt DTO 추가**

```python
from datetime import date

from .models.purchase_receipt import PurchaseReceiptItem


class PurchaseReceiptCreate(BaseModel):
    supplier_name: str
    posting_date: date
    items: list[PurchaseReceiptItem] = Field(default_factory=list)


class PurchaseReceiptUpdate(BaseModel):
    supplier_name: str | None = None
    posting_date: date | None = None
    items: list[PurchaseReceiptItem] | None = None
```

- [ ] **Step 4: models/purchase_receipt.py에서 Create/Update 제거**

- [ ] **Step 5: purchase_receipt_service 존재 확인 + 없으면 생성**

생성 시 collection은 `purchase_receipts`, submit 메서드는 입고 검수/재고 차감 로직을 포함해야 하나 이번 작업은 **경계 이동만** 허용. 기존 동작을 그대로 서비스 클래스로 옮긴다.

- [ ] **Step 6: routes/purchase_receipts.py 전환**

- Repository import 제거
- `PurchaseReceiptService` DI
- DTO import 교체

- [ ] **Step 7: 테스트 + E2E 회귀**

```bash
uv run --package oneerp-stock --directory services/scm/stock pytest -q
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```
Expected: 전부 PASS (입고 → 수주 → 송장 자동 분개 체인이 유지되어야 함).

- [ ] **Step 8: 커밋**

```bash
git add services/scm/stock/oneerp_stock_app/dto.py \
        services/scm/stock/oneerp_stock_app/models/purchase_receipt.py \
        services/scm/stock/oneerp_stock_app/routes/purchase_receipts.py \
        services/scm/stock/oneerp_stock_app/services/ \
        services/scm/stock/tests/unit/
git commit -m "refactor(stock): purchase_receipt DTO/route 경계 정리 (OE002/OE004)"
```

---

## Phase 4. Accounting OTC 슬라이스

### Task 4.1: accounting/dto.py + journal_entries DTO/route 전환

**Files:**
- Create: `services/finance/accounting/oneerp_accounting_app/dto.py`
- Modify: `services/finance/accounting/oneerp_accounting_app/models/journal_entry.py`
- Modify: `services/finance/accounting/oneerp_accounting_app/routes/journal_entries.py`
- Create: `services/finance/accounting/tests/unit/test_dto_boundary.py`
- Create: `services/finance/accounting/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 실패 테스트 작성**

`services/finance/accounting/tests/unit/test_dto_boundary.py`:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DTO_FILE = ROOT / "oneerp_accounting_app" / "dto.py"
JE_MODEL = ROOT / "oneerp_accounting_app" / "models" / "journal_entry.py"


def test_journal_entry_create_update가_dto에_있다() -> None:
    assert DTO_FILE.exists()
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class JournalEntryCreate" in text
    assert "class JournalEntryUpdate" in text


def test_journal_entry_model에는_dto가_없다() -> None:
    text = JE_MODEL.read_text(encoding="utf-8")
    assert "class JournalEntryCreate" not in text
    assert "class JournalEntryUpdate" not in text
```

`services/finance/accounting/tests/unit/test_route_boundary.py`:

```python
from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[3] / "oneerp_accounting_app" / "routes"


def test_journal_entries_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "journal_entries.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-accounting --directory services/finance/accounting pytest tests/unit/test_dto_boundary.py tests/unit/test_route_boundary.py -v
```

- [ ] **Step 3: dto.py 신설 + JournalEntry DTO 이동**

`services/finance/accounting/oneerp_accounting_app/dto.py`:

```python
"""accounting 서비스 DTO 집약 (OE004)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from .models.journal_entry import JournalEntryItem


class JournalEntryCreate(BaseModel):
    posting_date: date
    voucher_type: str = "Journal Entry"
    voucher_no: str | None = None
    items: list[JournalEntryItem] = Field(default_factory=list)
    total_debit: Decimal = Decimal(0)
    total_credit: Decimal = Decimal(0)


class JournalEntryUpdate(BaseModel):
    posting_date: date | None = None
    voucher_type: str | None = None
    voucher_no: str | None = None
    items: list[JournalEntryItem] | None = None
```

(실제 필드는 기존 Create/Update 그대로 이식)

- [ ] **Step 4: models/journal_entry.py에서 Create/Update 제거**

- [ ] **Step 5: journal_entry_service 확인 + 없으면 생성**

- [ ] **Step 6: routes/journal_entries.py 전환**

- [ ] **Step 7: 테스트 + E2E**

```bash
uv run --package oneerp-accounting --directory services/finance/accounting pytest -q
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```

- [ ] **Step 8: 커밋**

```bash
git add services/finance/accounting/oneerp_accounting_app/dto.py \
        services/finance/accounting/oneerp_accounting_app/models/journal_entry.py \
        services/finance/accounting/oneerp_accounting_app/routes/journal_entries.py \
        services/finance/accounting/oneerp_accounting_app/services/ \
        services/finance/accounting/tests/unit/
git commit -m "refactor(accounting): journal_entry DTO/route 경계 도입 (OE002/OE004)"
```

---

### Task 4.2: accounts_receivable DTO/route 전환

**Files:**
- Modify: `services/finance/accounting/oneerp_accounting_app/dto.py` (append)
- Modify: `services/finance/accounting/oneerp_accounting_app/models/accounts_receivable.py`
- Modify: `services/finance/accounting/oneerp_accounting_app/routes/accounts_receivable.py`
- Modify: `services/finance/accounting/tests/unit/test_dto_boundary.py`
- Modify: `services/finance/accounting/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 경계 테스트 확장**

`test_dto_boundary.py`에 추가:

```python
AR_MODEL = ROOT / "oneerp_accounting_app" / "models" / "accounts_receivable.py"


def test_accounts_receivable_create가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class AccountsReceivableCreate" in text


def test_accounts_receivable_model에는_dto가_없다() -> None:
    text = AR_MODEL.read_text(encoding="utf-8")
    assert "class AccountsReceivableCreate" not in text
```

`test_route_boundary.py`에 추가:

```python
def test_accounts_receivable_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "accounts_receivable.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-accounting --directory services/finance/accounting pytest tests/unit/test_dto_boundary.py tests/unit/test_route_boundary.py -v
```

- [ ] **Step 3: dto.py에 AR DTO 추가**

```python
class AccountsReceivableCreate(BaseModel):
    customer: str
    outstanding_amount: Decimal = Decimal(0)
    due_date: date | None = None
    voucher_no: str
```

(실제 필드는 기존 AccountsReceivableCreate 그대로)

- [ ] **Step 4: models/accounts_receivable.py에서 Create 제거**

- [ ] **Step 5: accounts_receivable_service 확인 + route 전환**

- [ ] **Step 6: 테스트 + E2E**

```bash
uv run --package oneerp-accounting --directory services/finance/accounting pytest -q
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```

- [ ] **Step 7: 커밋**

```bash
git add services/finance/accounting/oneerp_accounting_app/dto.py \
        services/finance/accounting/oneerp_accounting_app/models/accounts_receivable.py \
        services/finance/accounting/oneerp_accounting_app/routes/accounts_receivable.py \
        services/finance/accounting/oneerp_accounting_app/services/ \
        services/finance/accounting/tests/unit/
git commit -m "refactor(accounting): accounts_receivable DTO/route 경계 정리 (OE002/OE004)"
```

---

### Task 4.3: payment_entries DTO/route 전환

**Files:**
- Modify: `services/finance/accounting/oneerp_accounting_app/dto.py`
- Modify: `services/finance/accounting/oneerp_accounting_app/models/payment_entry.py`
- Modify: `services/finance/accounting/oneerp_accounting_app/routes/payment_entries.py`
- Modify: `services/finance/accounting/tests/unit/test_dto_boundary.py`
- Modify: `services/finance/accounting/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 경계 테스트 확장**

`test_dto_boundary.py`에 추가:

```python
PE_MODEL = ROOT / "oneerp_accounting_app" / "models" / "payment_entry.py"


def test_payment_entry_create_update가_dto에_있다() -> None:
    text = DTO_FILE.read_text(encoding="utf-8")
    assert "class PaymentEntryCreate" in text
    assert "class PaymentEntryUpdate" in text


def test_payment_entry_model에는_dto가_없다() -> None:
    text = PE_MODEL.read_text(encoding="utf-8")
    assert "class PaymentEntryCreate" not in text
    assert "class PaymentEntryUpdate" not in text
```

`test_route_boundary.py`에 추가:

```python
def test_payment_entries_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "payment_entries.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-accounting --directory services/finance/accounting pytest tests/unit/test_dto_boundary.py tests/unit/test_route_boundary.py -v
```

- [ ] **Step 3: dto.py에 PaymentEntry DTO 추가**

```python
from .models.payment_entry import PaymentEntryItem


class PaymentEntryCreate(BaseModel):
    payment_type: str
    party_type: str
    party_id: str
    party_name: str
    posting_date: date
    paid_amount: Decimal = Decimal(0)
    received_amount: Decimal = Decimal(0)
    reference_doctype: str | None = None
    reference_name: str | None = None
    items: list[PaymentEntryItem] = Field(default_factory=list)


class PaymentEntryUpdate(BaseModel):
    posting_date: date | None = None
    paid_amount: Decimal | None = None
    received_amount: Decimal | None = None
    items: list[PaymentEntryItem] | None = None
```

- [ ] **Step 4: models/payment_entry.py에서 Create/Update 제거**

- [ ] **Step 5: payment_entry_service 확인 + route 전환**

- [ ] **Step 6: 테스트 + E2E**

```bash
uv run --package oneerp-accounting --directory services/finance/accounting pytest -q
PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
  uv run pytest tests/e2e/test_order_to_cash_flow.py -v
```

- [ ] **Step 7: 커밋**

```bash
git add services/finance/accounting/oneerp_accounting_app/dto.py \
        services/finance/accounting/oneerp_accounting_app/models/payment_entry.py \
        services/finance/accounting/oneerp_accounting_app/routes/payment_entries.py \
        services/finance/accounting/oneerp_accounting_app/services/ \
        services/finance/accounting/tests/unit/
git commit -m "refactor(accounting): payment_entry DTO/route 경계 정리 (OE002/OE004)"
```

---

## Phase 5. 최종 회귀 + baseline 확정

### Task 5.1: OTC E2E 3회 연속 실행 확인

**Files:**
- (none — 읽기 전용 회귀)

- [ ] **Step 1: 3회 연속 OTC E2E 실행**

```bash
docker compose --profile infra up -d
for i in 1 2 3; do
  echo "=== 회차 $i ==="
  PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
    uv run pytest tests/e2e/test_order_to_cash_flow.py -v
done
```
Expected: 3회 모두 `3 passed` (로그인 / OTC 완전 플로우 / 재로그인).

- [ ] **Step 2: 실패 시**

어느 phase의 어느 task에서 시작했는지 `git bisect`로 찾고, 해당 task의 Step 6/7 E2E 단계에서 놓친 부분을 수정한다. 실패 원인이 payload 구조 변경이면 dto.py의 필드명/선택성을 models/의 Document와 교차 검증한다.

### Task 5.2: 최종 baseline 갱신 + 책임 매트릭스 문서화

**Files:**
- Modify: `.arch-baseline.json`
- Modify: `docs/governance/architecture/responsibility-matrix.md`

- [ ] **Step 1: 새 baseline 측정**

```bash
uv run python scripts/dev/check_layer_boundaries.py
```

OTC 3개 도메인의 OE002/OE004 위반이 감소했는지 숫자로 확인한다.

- [ ] **Step 2: baseline 갱신**

`.arch-baseline.json`의 OE002/OE004 값을 Step 1의 새 측정치로 교체.

- [ ] **Step 3: 책임 매트릭스에 진행 기록 추가**

`docs/governance/architecture/responsibility-matrix.md`의 `## 착수 조건` 하단에 다음 섹션을 추가:

```markdown
## 진행 기록

- 2026-04-14 Track A 완료 — scope SoT 복구, 책임 매트릭스, release gate, CI 정렬
- 2026-04-14 Track B/C (OTC vertical slice) 완료 — selling/stock/accounting 경로 3·2·3개에서 OE002/OE004 해소
```

- [ ] **Step 4: `--check`로 회귀 없음 확인**

```bash
uv run python scripts/dev/check_layer_boundaries.py --check
```
Expected: `✓ baseline 대비 위반 증가 없음`.

- [ ] **Step 5: 커밋**

```bash
git add .arch-baseline.json docs/governance/architecture/responsibility-matrix.md
git commit -m "chore(arch): OTC vertical slice 완료 baseline + 진행 기록"
```

---

## 성공 기준 (Definition of Done)

- [ ] `check_layer_boundaries.py`가 실제 `oneerp_*_app/` 구조를 검사한다
- [ ] `.arch-baseline.json`이 실제 구조 기준 숫자를 기록한다
- [ ] selling OTC 경로 3개 route (`sales_orders`, `delivery_notes`, `sales_invoices`)에서 Repository 직접 사용 0건
- [ ] stock OTC 경로 2개 route (`items`, `purchase_receipts`)에서 Repository 직접 사용 0건
- [ ] accounting OTC 경로 3개 route (`journal_entries`, `accounts_receivable`, `payment_entries`)에서 Repository 직접 사용 0건
- [ ] 각 서비스에 `dto.py`가 존재하며 OTC 관련 Create/Update가 거기 모여 있다
- [ ] 각 서비스의 관련 `models/*.py`에 Create/Update/Request/Response 클래스가 없다
- [ ] `tests/e2e/test_order_to_cash_flow.py`가 3회 연속 통과한다
- [ ] 각 도메인 단위 테스트(`test_dto_boundary.py`, `test_route_boundary.py`)가 모두 통과한다
