# 코딩 가이드 (Coding Guide)

첫 PR을 올리기까지 필요한 코딩 규칙 (coding conventions), 새 엔티티 추가 절차 (entity creation workflow), 품질 게이트 (quality gates)를 정리한다.

---

## 새 엔티티 추가 체크리스트 (New Entity Checklist)

새로운 비즈니스 엔티티 (business entity, 예: "배송업체 / Carrier")를 추가할 때 아래 5단계를 순서대로 따른다.

### 1. 모델 정의 (Define Model) --- `services/{서비스}/app/models/{엔티티}.py`

`BaseDocument`를 상속하여 도메인 모델 (domain model)을 정의한다.
Create/Update 스키마 (schema)도 함께 정의한다.

```python
"""배송업체(Carrier) 모델."""

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CarrierCreate(BaseModel):
    """배송업체 생성 요청 스키마."""

    carrier_name: str
    carrier_type: str = "domestic"  # domestic / international
    contact: dict | None = None


class CarrierUpdate(BaseModel):
    """배송업체 수정 요청 스키마."""

    carrier_name: str | None = None
    carrier_type: str | None = None
    contact: dict | None = None


class Carrier(BaseDocument):
    """배송업체 마스터.

    naming prefix: CARR
    """

    carrier_name: str = ""
    carrier_type: str = "domestic"
    contact: dict | None = None
```

### 2. 라우터 작성 (Create Router) --- `services/{서비스}/app/routes/{엔티티_복수}.py`

CRUD 5종 (5 CRUD operations: Create, List, Read, Update, Delete)을 구현한다.

```python
"""배송업체(Carrier) CRUD 라우터."""

from fastapi import APIRouter, HTTPException
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from app.deps import CurrentUserDep
from app.models.carrier import Carrier, CarrierCreate, CarrierUpdate

router = APIRouter(prefix="/api/v1/carriers", tags=["배송업체"])

_COLLECTION = "carriers"
_PREFIX = "CARR"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201)
def 배송업체_생성(body: CarrierCreate, user: CurrentUserDep) -> dict:
    """배송업체를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    carrier = Carrier(
        _id=doc_id,
        tenant_id=user.tenant_id,
        carrier_name=body.carrier_name,
        carrier_type=body.carrier_type,
        contact=body.contact,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(carrier)
    return {"_id": doc_id, **body.model_dump()}


@router.get("")
def 배송업체_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """배송업체 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count()
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}")
def 배송업체_조회(doc_id: str, user: CurrentUserDep) -> dict:
    """배송업체를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="배송업체를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}")
def 배송업체_수정(doc_id: str, body: CarrierUpdate, user: CurrentUserDep) -> dict:
    """배송업체를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="배송업체를 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {**doc, **update_data}


@router.delete("/{doc_id}", status_code=204)
def 배송업체_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """배송업체를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="배송업체를 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
```

### 3. 테스트 작성 (Write Tests) --- `services/{서비스}/tests/unit/test_{엔티티_복수}.py`

최소 3개 테스트 (minimum 3 tests): 생성 정상 (create success), 목록 조회 (list), 404 처리 (404 handling).

```python
"""배송업체(Carrier) CRUD 엔드포인트 테스트."""

from unittest.mock import MagicMock, patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("app.routes.carriers._get_repo")
@patch("app.routes.carriers.generate_name", return_value="CARR-2026-00001")
def test_배송업체_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/carriers -- 정상 생성 시 201과 _id를 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/carriers",
        json={"carrier_name": "CJ대한통운", "carrier_type": "domestic"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["_id"] == "CARR-2026-00001"


@patch("app.routes.carriers._get_repo")
def test_배송업체_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/carriers -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "CARR-001", "carrier_name": "한진택배"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/carriers?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


@patch("app.routes.carriers._get_repo")
def test_배송업체_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/carriers/{doc_id} -- 없는 배송업체는 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/carriers/NOT-EXIST")
    assert response.status_code == 404
```

### 4. main.py에 라우터 등록 (Register Router in main.py) --- `services/{서비스}/app/main.py`

```python
from .routes.carriers import router as carriers_router

# 기존 라우터 등록 아래에 추가 (Add below existing router registrations)
app.include_router(carriers_router)
```

### 5. (선택) FE EntityConfig 추가 (Optional: Add FE EntityConfig) --- `apps/web/lib/modules/{엔티티}.ts`

EntityConfig를 정의하면 목록/상세/생성/수정 페이지가 자동 생성 (auto-generated)된다.

```typescript
import type { EntityConfig } from "@/lib/crud/types";

export const carrierConfig: EntityConfig = {
  entity: "carriers",
  service: "selling",
  label: { singular: "배송업체", plural: "배송업체 목록" },
  columns: [
    { key: "_id", header: "ID", width: "200px" },
    { key: "carrier_name", header: "배송업체명" },
    { key: "carrier_type", header: "유형", width: "100px" },
  ],
  formFields: [
    { key: "carrier_name", label: "배송업체명", type: "text", required: true, colSpan: 6 },
    {
      key: "carrier_type",
      label: "유형",
      type: "select",
      colSpan: 6,
      options: [
        { value: "domestic", label: "국내" },
        { value: "international", label: "국제" },
      ],
    },
  ],
};
```

FE 페이지 파일 (page file)은 `apps/web/app/(selling)/carriers/page.tsx` 등에 생성:

```tsx
import { EntityListPage } from "@/components/crud/entity-list-page";
import { carrierConfig } from "@/lib/modules/carriers";

export default async function Page(props: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const searchParams = await props.searchParams;
  return <EntityListPage config={carrierConfig} searchParams={searchParams} />;
}
```

---

## 코딩 규칙 (Coding Conventions)

### 전역 (Global)

- **모든 코드/주석은 한국어 (All code/comments in Korean)**로 작성한다.
- **테스트 없는 기능은 존재할 수 없다 (No feature without tests).**
- 요구된 것만 구현한다. 요청되지 않은 유연성/범용화 금지 (No over-engineering).

### Python (BE)

| 규칙 (Rule) | 설명 (Description) |
|------|------|
| `from __future__ import annotations` | 모든 `.py` 파일 최상단에 필수 (Required at top of every `.py` file, FA rule) |
| `print()` 사용 금지 (No print()) | `logging` 모듈 사용 (Use `logging` module, T20 rule). `setup_logging`이 JSON 구조화 로그 제공 |
| 환경변수 `ONEERP_` 접두사 (Env var prefix) | 하드코딩 금지 (No hardcoding). `CoreSettings` 또는 서비스별 `Settings` 사용 |
| DI: `Annotated[T, Depends()]` | `deps.py`에 타입 별칭 정의 후 라우터에서 사용 (Define type aliases in `deps.py`) |
| 모델: `BaseDocument` 상속 (Inherit BaseDocument) | 모든 비즈니스 엔티티는 `oneerp_core.document.BaseDocument` 상속 |
| Repository 패턴 (Repository Pattern) | DB 직접 접근 금지 (No direct DB access). `Repository` 클래스를 통해서만 CRUD |

### TypeScript (FE)

| 규칙 (Rule) | 설명 (Description) |
|------|------|
| EntityConfig 기반 (EntityConfig-based) | 새 모듈은 `lib/modules/`에 EntityConfig만 정의하면 CRUD UI 자동 생성 |
| Biome 포맷/린트 (Biome Format/Lint) | `pnpm --filter @oneerp/web lint`로 검사 |
| App Router | `app/(그룹명)/엔티티/page.tsx` 구조 (Route group structure) |

---

## 의존성 주입 패턴 (Dependency Injection Pattern)

서비스별 `deps.py`에 DI 타입 별칭 (type alias)을 정의한다.

```python
# services/{서비스}/app/deps.py
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from oneerp_core.auth import CurrentUser, get_current_user

from .config import Settings, get_settings


def _get_user() -> CurrentUser:
    """현재 인증된 사용자를 주입한다."""
    return get_current_user()


SettingsDep = Annotated[Settings, Depends(get_settings)]
CurrentUserDep = Annotated[CurrentUser, Depends(_get_user)]
```

라우터에서 사용 (Usage in routers):

```python
@router.post("", status_code=201)
def 엔티티_생성(body: CreateSchema, user: CurrentUserDep) -> dict:
    repo = _get_repo(user.tenant_id)  # tenant_id는 user에서 추출
    ...
```

---

## 서비스별 설정 패턴 (Per-service Settings Pattern)

각 서비스는 `CoreSettings`를 상속하여 서비스 고유 설정을 추가한다.
Each service extends `CoreSettings` to add service-specific configuration.

```python
# services/{서비스}/app/config.py
from __future__ import annotations

from functools import lru_cache

from oneerp_core.config import CoreSettings


class Settings(CoreSettings):
    """서비스별 설정 --- CoreSettings 상속."""

    service_name: str = "서비스명"
    # 서비스 고유 설정 추가 가능 (Add service-specific settings here)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings 싱글턴을 반환한다."""
    return Settings()
```

---

## 품질 게이트 (Quality Gates)

PR을 올리기 전에 반드시 통과해야 하는 게이트이다.
These gates must pass before submitting a PR.

### BE (순서대로 / In Order)

```bash
# 1. 포맷 검사 (Format check)
uv run ruff format --check .

# 2. 린트 (Lint)
uv run ruff check .

# 3. 타입 검사 (Type check)
uv run ty check .

# 4. 단위 테스트 (Unit tests)
uv run pytest -m "not integration and not e2e" packages/
uv run --directory services/{서비스} pytest tests/ -m "not integration and not e2e" -q
```

### FE (순서대로 / In Order)

```bash
# 1. Biome 린트/포맷 (Biome lint/format)
pnpm --filter @oneerp/web lint

# 2. TypeScript 타입 검사 (TypeScript type check)
pnpm --filter @oneerp/web typecheck

# 3. Next.js 빌드 (Next.js build)
pnpm --filter @oneerp/web build
```

### 전체 한 번에 (Run All At Once)

```bash
./scripts/ci/run.sh
```

> **린트 에러 1건이라도 있으면 커밋/병합/푸시 불가.**
> **Even a single lint error blocks commit/merge/push.**
>
> **테스트 FAILED 1건이라도 있으면 커밋/병합/푸시 불가.**
> **Even a single test failure blocks commit/merge/push.**

---

## Git 규칙 (Git Conventions)

### 커밋 메시지 (Commit Messages)

```
{타입 / type}: {한국어 설명 / Korean description}

타입: feat | fix | refactor | docs | test | chore
```

예시 (Examples):

```
feat: 배송업체 CRUD API 구현
fix: 고객 목록 페이지네이션 total_count 오류 수정
test: 배송업체 404 응답 테스트 추가
```

### PR 전 필수 절차 (Pre-PR Checklist)

1. 품질 게이트 전체 통과 확인 (All quality gates pass)
2. 변경과 관련 없는 파일이 포함되지 않았는지 확인 (No unrelated files)
3. 테스트가 변경사항을 커버하는지 확인 (Tests cover changes)

---

## 자주 하는 실수 (Common Mistakes)

### 1. `app` 패키지명 충돌 (Package Name Conflict)

모든 서비스가 `app/` 패키지를 사용하므로, uvicorn 실행 시 `--directory`가 없으면 잘못된 서비스가 로드된다.
All services use the `app/` package, so running uvicorn without `--directory` may load the wrong service.

```bash
# 잘못된 실행 (Wrong — which service's app loads is undefined)
uv run uvicorn app.main:app --port 8001

# 올바른 실행 (Correct)
uv run --package oneerp-selling --directory services/selling uvicorn app.main:app --port 8001
```

### 2. tenant_id 누락 걱정 (Worrying About Missing tenant_id)

`Repository`가 모든 쿼리에 `tenant_id`를 자동으로 삽입하므로, 라우터에서 직접 필터링할 필요 없다.
`Repository` auto-injects `tenant_id` into all queries, so no manual filtering is needed.

```python
# 불필요 (Unnecessary — Repository handles this)
repo.find_many({"tenant_id": user.tenant_id})

# 올바른 사용 (Correct usage)
repo = _get_repo(user.tenant_id)  # 생성 시 tenant_id 전달 (Pass tenant_id at creation)
repo.find_many()                   # 자동으로 tenant 격리됨 (Auto tenant isolation)
```

### 3. date 타입을 datetime으로 변환하지 않음 (Not Converting date to datetime)

FerretDB(BSON)는 `date` 타입을 직접 저장할 수 없다. `Repository._coerce_dates()`가 자동 변환하므로 모델에서 `date`를 사용해도 된다.
FerretDB(BSON) cannot store `date` directly. `Repository._coerce_dates()` handles conversion automatically.

### 4. `from __future__ import annotations` 누락 (Missing Future Annotations)

모든 `.py` 파일 최상단에 필수. 누락 시 ruff에서 FA100 에러가 발생한다.
Required at the top of every `.py` file. Missing it triggers ruff FA100 error.

### 5. `print()` 사용 (Using print())

ruff의 T20 규칙으로 차단된다. `logging` 모듈을 사용한다.
Blocked by ruff's T20 rule. Use the `logging` module instead.

```python
import logging

logger = logging.getLogger(__name__)
logger.info("처리 완료: doc_id=%s", doc_id)
```

### 6. 테스트에서 실제 DB 연결 (Real DB Connection in Tests)

단위 테스트 (unit tests)는 `unittest.mock.patch`로 Repository와 `generate_name`을 모킹 (mock)한다.
실제 FerretDB 연결이 필요한 테스트는 `@pytest.mark.integration` 마커를 붙인다.
