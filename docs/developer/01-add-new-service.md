# 새 서비스 추가 방법 (How to Add a New Service)

OneERP 모노레포에 새 백엔드 마이크로서비스 (microservice)를 추가하는 절차를 안내한다.
This guide walks through adding a new backend microservice to the OneERP monorepo.

---

## Step 1: 디렉토리 생성 (Create Directory)

`services/` 하위에 서비스 디렉토리 구조를 생성한다.
Create the service directory structure under `services/`.

```bash
mkdir -p services/{서비스명}/app/models
mkdir -p services/{서비스명}/app/routes
mkdir -p services/{서비스명}/app/services
mkdir -p services/{서비스명}/tests/unit
touch services/{서비스명}/app/__init__.py
touch services/{서비스명}/app/models/__init__.py
touch services/{서비스명}/app/routes/__init__.py
touch services/{서비스명}/app/services/__init__.py
touch services/{서비스명}/tests/__init__.py
touch services/{서비스명}/tests/unit/__init__.py
```

---

## Step 2: pyproject.toml 작성 (Write pyproject.toml)

uv workspace member로 등록될 `pyproject.toml`을 작성한다.
기존 서비스(예: `services/expenses/pyproject.toml`)를 참고한다.

```toml
[project]
name = "oneerp-{서비스명}"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "oneerp-core",
]

[tool.uv.sources]
oneerp-core = { workspace = true }

[dependency-groups]
dev = ["httpx>=0.28.0", "pytest>=9.0.2"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --import-mode=importlib"
```

루트 `pyproject.toml`의 `[tool.uv.workspace]` members에 새 서비스 경로를 추가한다.
Add the new service path to `[tool.uv.workspace]` members in root `pyproject.toml`.

---

## Step 3: 모델 정의 (Define Models)

`services/{서비스명}/app/models/` 디렉토리에 Pydantic 모델을 정의한다.
모든 비즈니스 엔티티는 `BaseDocument`를 상속해야 한다.
All business entities must inherit from `BaseDocument`.

```python
"""예시 엔티티(Example) 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ExampleCreate(BaseModel):
    """생성 요청 스키마 (Create request schema)."""

    name: str
    description: str = ""


class ExampleUpdate(BaseModel):
    """수정 요청 스키마 (Update request schema)."""

    name: str | None = None
    description: str | None = None


class Example(BaseDocument):
    """예시 엔티티 (Example entity).

    naming prefix: EXM
    """

    name: str = ""
    description: str = ""
```

---

## Step 4: EntityMeta 등록 (Register EntityMeta)

`services/{서비스명}/app/entities.py`에 `EntityMeta`를 선언한다.
`EntityMeta`에 등록하면 `create_service_app`이 자동 CRUD 엔드포인트를 생성한다.
Registering in `EntityMeta` lets `create_service_app` auto-generate CRUD endpoints.

커스텀 로직이 필요한 엔티티는 `ENTITY_METAS`에 포함하지 않고, `extra_routers`로 직접 관리한다.
Entities with custom logic should be excluded from `ENTITY_METAS` and managed via `extra_routers`.

```python
"""서비스 엔티티 메타 선언."""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.example import Example, ExampleCreate, ExampleUpdate

EXAMPLE = EntityMeta(
    collection="examples",
    prefix="EXM",
    api_path="/api/v1/examples",
    tag="예시",
    resource="example",
    model=Example,
    create_schema=ExampleCreate,
    update_schema=ExampleUpdate,
    archetype="master",  # 또는 "transaction" (or "transaction")
    not_found_message="예시를 찾을 수 없습니다",
)

# 자동 CRUD 생성 대상 (Auto CRUD generation targets)
ENTITY_METAS: list[EntityMeta] = [EXAMPLE]
```

---

## Step 5: main.py 작성 (Write main.py)

`create_service_app` 팩토리 (factory)를 사용하여 FastAPI 앱을 생성한다.
미들웨어 (middleware), 예외 핸들러 (exception handler), 헬스체크 (health check)가 자동으로 등록된다.

```python
"""OneERP {서비스명} 서비스."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS

app = create_service_app(
    service_name="{서비스명}",
    entity_metas=ENTITY_METAS,
    # extra_routers=[...],  # 커스텀 라우터가 있으면 추가 (Add custom routers if needed)
)
```

### config.py 작성 (Write config.py)

```python
"""서비스별 설정 (Service-specific settings)."""

from __future__ import annotations

from functools import lru_cache

from oneerp_core.config import CoreSettings


class Settings(CoreSettings):
    """서비스별 설정 --- CoreSettings 상속."""

    service_name: str = "{서비스명}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings 싱글턴을 반환한다 (Return Settings singleton)."""
    return Settings()
```

### deps.py 작성 (Write deps.py)

```python
"""의존성 주입 (Dependency Injection)."""

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

---

## Step 6: Dockerfile 작성 (Write Dockerfile)

`services/{서비스명}/Dockerfile`에 컨테이너 이미지 빌드 파일을 작성한다.

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# uv 설치 (Install uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 설치 (Install dependencies)
COPY pyproject.toml .
COPY packages/core/ /packages/core/
RUN uv sync --no-dev

# 소스 복사 (Copy source)
COPY services/{서비스명}/app/ ./app/

EXPOSE {포트}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{포트}"]
```

> **빌드는 반드시 `apple/container`로 linux/amd64만 빌드한다.**
> **Builds must use `apple/container` targeting linux/amd64 only.**

---

## Step 7: Helm 차트 생성 (Create Helm Chart)

`deploy/helm/{서비스명}/` 디렉토리에 Helm 차트를 생성한다.
기존 서비스 차트를 참고하여 `Chart.yaml`, `values.yaml`, `templates/`를 작성한다.
Reference existing service charts for `Chart.yaml`, `values.yaml`, and `templates/`.

---

## Step 8: CI 파이프라인 등록 (Register in CI Pipeline)

`CI 파이프라인` 또는 CI 설정에 새 서비스의 빌드/테스트/배포 파이프라인을 추가한다.
Add build/test/deploy pipeline for the new service in `CI 파이프라인` or CI configuration.

필수 품질 게이트 (Required quality gates):

```bash
# 서비스 디렉토리에서 테스트 실행 (Run tests in service directory)
uv run --directory services/{서비스명} pytest tests/ -m "not integration and not e2e" -q
```

---

## 체크리스트 (Checklist)

새 서비스 추가 후 확인사항:

- [ ] `pyproject.toml` 작성 및 루트 workspace에 등록 (Created and registered in root workspace)
- [ ] `uv sync` 성공 (uv sync succeeds)
- [ ] `uvicorn` 정상 기동 (uvicorn starts without errors)
- [ ] `/health` 엔드포인트 응답 확인 (Health endpoint responds)
- [ ] Swagger UI 접근 가능 (`/docs` accessible)
- [ ] 단위 테스트 통과 (Unit tests pass)
- [ ] 품질 게이트 전체 통과 (All quality gates pass)
