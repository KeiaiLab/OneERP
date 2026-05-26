# 테스트 가이드 (Testing Guide)

OneERP의 테스트 전략 (testing strategy), 테스트 종류별 작성법, 실행 방법을 안내한다.
This guide covers the OneERP testing strategy, how to write each type of test, and how to run them.

---

## 단위 테스트 (Unit Tests)

단위 테스트는 외부 의존성 (DB, 네트워크 등)을 모킹 (mock)하여 빠르게 실행된다.
모든 새 기능에는 반드시 단위 테스트가 포함되어야 한다.
Unit tests mock external dependencies (DB, network) and run fast.
Every new feature must include unit tests.

### 위치 (Location)

```
services/{서비스명}/tests/unit/test_{엔티티_복수}.py
packages/core/tests/unit/test_{모듈}.py
```

### 작성 패턴 (Writing Pattern)

```python
"""고객(Customer) CRUD 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("app.routes.customers._get_repo")
@patch("app.routes.customers.generate_name", return_value="CUST-2026-00001")
def test_고객_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/customers -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/customers",
        json={"customer_name": "테스트 고객"},
    )
    assert response.status_code == 201
    assert response.json()["_id"] == "CUST-2026-00001"


@patch("app.routes.customers._get_repo")
def test_고객_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/customers/{id} -- 없는 문서는 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/customers/NOT-EXIST")
    assert response.status_code == 404
```

### 실행 (Run)

```bash
# 코어 패키지 테스트 (Core package tests)
uv run pytest -m "not integration and not e2e" packages/ -q

# 서비스별 테스트 (Per-service tests, --directory required)
uv run --directory services/selling pytest tests/ -m "not integration and not e2e" -q

# 전체 서비스 테스트 (All service tests)
uv run pytest -m "not integration and not e2e" services/ packages/ -q
```

---

## 통합 테스트 (Integration Tests)

통합 테스트는 실제 FerretDB 연결로 데이터 흐름 (data flow)을 검증한다.
`@pytest.mark.integration` 마커를 붙여 단위 테스트와 분리한다.
Integration tests verify data flow with a real FerretDB connection.
Use the `@pytest.mark.integration` marker to separate from unit tests.

### 작성 패턴 (Writing Pattern)

```python
"""고객 통합 테스트 (Customer integration tests)."""

from __future__ import annotations

import pytest
from oneerp_core.repository import Repository


@pytest.mark.integration
def test_고객_생성_후_조회() -> None:
    """생성한 고객을 ID로 조회할 수 있다.
    Created customer can be retrieved by ID.
    """
    repo = Repository("customers", tenant_id="test-tenant")
    doc = {"_id": "CUST-TEST-001", "customer_name": "통합테스트 고객", "tenant_id": "test-tenant"}
    repo.insert(doc)

    result = repo.find_by_id("CUST-TEST-001")
    assert result is not None
    assert result["customer_name"] == "통합테스트 고객"

    # 정리 (Cleanup)
    repo.delete_by_id("CUST-TEST-001")
```

### 실행 (Run)

```bash
# FerretDB가 실행 중이어야 한다 (FerretDB must be running)
docker compose up -d

# 통합 테스트 실행 (Run integration tests)
uv run --directory services/selling pytest tests/ -m integration -q
```

---

## E2E 테스트 (End-to-End Tests)

E2E 테스트는 여러 서비스를 아우르는 비즈니스 시나리오 (business scenario)를 검증한다.
`tests/e2e/` 디렉토리에 위치한다.
E2E tests verify business scenarios spanning multiple services.
Located in the `tests/e2e/` directory.

### 실행 (Run)

```bash
# 모든 관련 서비스가 실행 중이어야 한다 (All related services must be running)
uv run pytest -m e2e tests/e2e/ -q
```

---

## conftest.py 패턴 (Conftest Pattern)

`conftest.py`에 공통 픽스처 (common fixtures)를 정의하여 테스트 코드 중복을 줄인다.

### 서비스별 conftest (Per-service conftest)

```python
"""테스트 공통 픽스처 (Common test fixtures)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """FastAPI 테스트 클라이언트를 생성한다.
    Create a FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture
def mock_repo() -> MagicMock:
    """모킹된 Repository를 반환한다.
    Return a mocked Repository.
    """
    repo = MagicMock()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    return repo


@pytest.fixture
def mock_user() -> dict:
    """테스트용 사용자 정보를 반환한다.
    Return test user info.
    """
    return {
        "sub": "test-user",
        "tenant_id": "test-tenant",
        "roles": ("admin",),
        "user_tier": "super_admin",
        "is_super_admin": True,
    }
```

---

## Mock 패턴 (Mock Patterns)

### Repository 모킹 (Repository Mocking)

가장 빈번한 모킹 대상은 `_get_repo`와 `generate_name`이다.

```python
# 패턴 1: 함수 데코레이터 (Decorator pattern)
@patch("app.routes.items._get_repo")
@patch("app.routes.items.generate_name", return_value="ITEM-2026-00001")
def test_아이템_생성(mock_name, mock_repo):
    mock_repo.return_value = MagicMock()
    ...

# 패턴 2: context manager
def test_아이템_조회():
    with patch("app.routes.items._get_repo") as mock_repo:
        repo = MagicMock()
        repo.find_by_id.return_value = {"_id": "ITEM-001", "item_name": "테스트"}
        mock_repo.return_value = repo
        ...
```

### 인증 사용자 모킹 (Auth User Mocking)

`ONEERP_DEBUG=true`일 때 더미 사용자 (dummy user)가 자동으로 주입되므로, 대부분의 단위 테스트에서 별도 인증 모킹이 불필요하다.
With `ONEERP_DEBUG=true`, a dummy user is auto-injected, so most unit tests don't need auth mocking.

필요한 경우 (When needed):

```python
from unittest.mock import patch
from oneerp_core.auth import CurrentUser

mock_user = CurrentUser(
    sub="user-001",
    tenant_id="tenant-001",
    roles=("manager",),
    permissions=("sales_order:create",),
    user_tier="regular",
)

with patch("app.deps._get_user", return_value=mock_user):
    ...
```

---

## 테스트 명명 규칙 (Test Naming Convention)

```python
# 패턴 (Pattern): test_{기능}_{시나리오}_{기대_결과}
def test_고객_생성_정상_201():           # 정상 케이스 (Success case)
def test_고객_조회_미존재_404():         # 에러 케이스 (Error case)
def test_판매주문_제출_이미제출_409():    # 비즈니스 규칙 위반 (Business rule violation)
def test_경비청구_승인_권한부족_403():    # 권한 관련 (Permission related)
```

테스트 docstring에는 HTTP 메서드와 경로를 포함한다 (Include HTTP method and path in docstring):

```python
def test_고객_생성_정상_201() -> None:
    """POST /api/v1/customers -- 정상 생성 시 201과 _id를 반환한다."""
```

---

## 테스트 커버리지 최소 요구사항 (Minimum Test Coverage Requirements)

새 엔티티 (new entity) 추가 시 최소 3개 테스트:

1. **생성 정상 (Create success)**: POST 201 + _id 반환 확인
2. **목록 조회 (List)**: GET 200 + 페이지네이션 구조 확인
3. **404 처리 (Not found)**: GET 404 반환 확인

비즈니스 로직 (business logic) 추가 시:

- **정상 경로 (Happy path)**: 기대 결과 확인
- **에러 경로 (Error path)**: 유효하지 않은 입력/상태에서 적절한 에러 반환
- **경계 조건 (Edge cases)**: 0, 빈 값, 최대값 등

> **테스트 FAILED 1건이라도 있으면 커밋/병합/푸시 불가.**
> **Even a single test failure blocks commit/merge/push.**
