# Gateway Identity Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** gateway의 `auth + users + me`를 identity 서브도메인으로 재구성해 `route → service`, `models → dto`, `presentation 분리` 경계를 확립한다.

**Architecture:** 외부 API 경로와 응답 계약은 유지한다. 내부에서는 `dto.py`, `token_service.py`, `permission_service.py`, `auth_service.py`, `user_service.py`, `user_presenter.py`, `me_service.py`를 도입해 라우트의 Repository 직접 접근과 파생 계산을 제거한다.

**Tech Stack:** Python 3.14, FastAPI, Pydantic v2, pytest, uv workspace, ruff

---

## Task 1: DTO 경계 분리

**Files:**
- Create: `services/platform/gateway/oneerp_gateway_app/dto.py`
- Modify: `services/platform/gateway/oneerp_gateway_app/models/user.py`
- Modify: `services/platform/gateway/oneerp_gateway_app/routes/auth.py`
- Modify: `services/platform/gateway/oneerp_gateway_app/routes/users.py`
- Test: `services/platform/gateway/tests/unit/test_dto_boundary.py`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`services/platform/gateway/tests/unit/test_dto_boundary.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_gateway_app"


def test_user_dto가_dto_py에_존재한다() -> None:
    text = (ROOT / "dto.py").read_text(encoding="utf-8")
    assert "class UserCreate" in text
    assert "class UserUpdate" in text


def test_user_model에는_request_dto가_없다() -> None:
    text = (ROOT / "models" / "user.py").read_text(encoding="utf-8")
    assert "class UserCreate" not in text
    assert "class UserUpdate" not in text
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_dto_boundary.py -v
```
Expected: FAIL — `dto.py`가 아직 없다.

- [ ] **Step 3: 최소 구현 — dto.py 생성**

`services/platform/gateway/oneerp_gateway_app/dto.py`에 아래를 추가한다.

```python
from __future__ import annotations

from pydantic import BaseModel, Field

from .models.user import UserAuthProvider, UserTier


class LoginRequest(BaseModel):
    username: str = Field(description="사용자명")
    password: str = Field(description="비밀번호")


class TokenResponse(BaseModel):
    access_token: str = Field(description="액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 유형")
    expires_in: int = Field(description="만료 시간(초)")


class UserCreate(BaseModel):
    username: str = Field(description="사용자명")
    email: str = Field(default="", description="이메일")
    full_name: str = Field(default="", description="성명")
    is_active: bool = Field(default=True, description="활성 여부")
    role: str = Field(default="", description="역할 (하위 호환)")
    roles: list[str] = Field(default_factory=list, description="역할 목록 (다중 역할)")
    company_id: str = Field(default="", description="소속 회사 ID")
    department_name: str = Field(default="", description="소속 부서명")
    auth_provider: UserAuthProvider = Field(default=UserAuthProvider.PASSWORD)
    oidc_subject: str = Field(default="", description="OIDC subject")
    user_tier: UserTier = Field(default=UserTier.REGULAR)
    is_super_admin: bool = Field(default=False)
    password: str = Field(default="", description="비밀번호")


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    role: str | None = None
    roles: list[str] | None = None
    company_id: str | None = None
    department_name: str | None = None
    auth_provider: UserAuthProvider | None = None
    oidc_subject: str | None = None
    user_tier: UserTier | None = None
    is_super_admin: bool | None = None
    password: str | None = None
```

- [ ] **Step 4: models/user.py에서 DTO 제거**

`services/platform/gateway/oneerp_gateway_app/models/user.py`에서 `UserCreate`, `UserUpdate` 클래스 블록을 삭제하고 enum + `User`만 남긴다.

- [ ] **Step 5: 라우트 import 교체**

`routes/auth.py`, `routes/users.py`에서 DTO import를 `..dto`로 교체한다.

- [ ] **Step 6: 테스트 통과 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_dto_boundary.py -v
```
Expected: PASS

- [ ] **Step 7: 커밋**

```bash
git add services/platform/gateway/oneerp_gateway_app/dto.py \
        services/platform/gateway/oneerp_gateway_app/models/user.py \
        services/platform/gateway/oneerp_gateway_app/routes/auth.py \
        services/platform/gateway/oneerp_gateway_app/routes/users.py \
        services/platform/gateway/tests/unit/test_dto_boundary.py
git commit -m "refactor(gateway): user/auth DTO를 dto.py로 분리"
```

---

## Task 2: Token + Permission 서비스 추출

**Files:**
- Create: `services/platform/gateway/oneerp_gateway_app/services/token_service.py`
- Create: `services/platform/gateway/oneerp_gateway_app/services/permission_service.py`
- Modify: `services/platform/gateway/oneerp_gateway_app/routes/auth.py`
- Test: `services/platform/gateway/tests/unit/test_token_service.py`

- [ ] **Step 1: 실패 테스트 작성**

`services/platform/gateway/tests/unit/test_token_service.py` 생성:

```python
from __future__ import annotations

from oneerp_gateway_app.services.token_service import create_refresh_token_payload


def test_refresh_payload은_refresh_type을_가진다() -> None:
    payload = create_refresh_token_payload(username="demo", tenant_id="t1")
    assert payload["type"] == "refresh"
    assert payload["sub"] == "demo"
    assert payload["tenant_id"] == "t1"
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_token_service.py -v
```
Expected: FAIL — `token_service.py` 없음.

- [ ] **Step 3: token_service.py 최소 구현**

`routes/auth.py`의 `_create_access_token`, `_create_refresh_token`, `_set_auth_cookies`를 옮겨 `token_service.py`를 만든다.

- [ ] **Step 4: permission_service.py 최소 구현**

`routes/auth.py`의 `_resolve_permissions()`를 `permission_service.py`로 이동한다.

- [ ] **Step 5: auth route가 새 서비스 import만 사용하도록 교체**

`routes/auth.py`에서 위 함수 정의를 제거하고 서비스 호출로 바꾼다.

- [ ] **Step 6: 테스트 통과 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_token_service.py tests/unit/test_auth_routes.py -v
```
Expected: PASS

- [ ] **Step 7: 커밋**

```bash
git add services/platform/gateway/oneerp_gateway_app/services/token_service.py \
        services/platform/gateway/oneerp_gateway_app/services/permission_service.py \
        services/platform/gateway/oneerp_gateway_app/routes/auth.py \
        services/platform/gateway/tests/unit/test_token_service.py
git commit -m "refactor(gateway): token과 permission 서비스를 추출"
```

---

## Task 3: Auth 유스케이스를 auth_service로 이동

**Files:**
- Create: `services/platform/gateway/oneerp_gateway_app/services/auth_service.py`
- Modify: `services/platform/gateway/oneerp_gateway_app/routes/auth.py`
- Test: `services/platform/gateway/tests/unit/test_auth_service.py`
- Test: `services/platform/gateway/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 실패 테스트 작성**

`services/platform/gateway/tests/unit/test_route_boundary.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_gateway_app" / "routes"


def test_auth_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "auth.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_route_boundary.py::test_auth_route는_repository를_직접_사용하지_않는다 -v
```
Expected: FAIL — 현재 auth route가 Repository를 직접 사용한다.

- [ ] **Step 3: auth_service.py 구현**

다음 책임을 `auth_service.py`로 이동한다.

- tenant header fallback
- 사용자 조회
- password hash 비교
- active 여부 검증
- refresh token 검증 후 사용자 재조회
- logout cookie 삭제에 필요한 응답 조작 helper

- [ ] **Step 4: auth route를 thin controller로 축소**

`routes/auth.py`는 request/response DTO와 `auth_service` 호출만 남긴다.

- [ ] **Step 5: 테스트 통과 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_auth_service.py tests/unit/test_auth_routes.py tests/unit/test_route_boundary.py -v
```
Expected: PASS

- [ ] **Step 6: 커밋**

```bash
git add services/platform/gateway/oneerp_gateway_app/services/auth_service.py \
        services/platform/gateway/oneerp_gateway_app/routes/auth.py \
        services/platform/gateway/tests/unit/test_auth_service.py \
        services/platform/gateway/tests/unit/test_route_boundary.py
git commit -m "refactor(gateway): auth route를 identity service로 분리"
```

---

## Task 4: User 유스케이스 + Presenter 분리

**Files:**
- Create: `services/platform/gateway/oneerp_gateway_app/services/user_service.py`
- Create: `services/platform/gateway/oneerp_gateway_app/services/user_presenter.py`
- Modify: `services/platform/gateway/oneerp_gateway_app/routes/users.py`
- Test: `services/platform/gateway/tests/unit/test_user_presenter.py`
- Test: `services/platform/gateway/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 실패 테스트 작성**

`services/platform/gateway/tests/unit/test_route_boundary.py`에 추가:

```python
def test_users_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "users.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text
```

`services/platform/gateway/tests/unit/test_user_presenter.py` 생성:

```python
from __future__ import annotations

from oneerp_gateway_app.services.user_presenter import status_badge_for


def test_inactive_user는_inactive_badge를_가진다() -> None:
    assert status_badge_for({"is_active": False}) == "inactive_user"
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_user_presenter.py tests/unit/test_route_boundary.py::test_users_route는_repository를_직접_사용하지_않는다 -v
```
Expected: FAIL

- [ ] **Step 3: presenter 구현**

`routes/users.py`의 아래 함수들을 `user_presenter.py`로 이동한다.

- `_status_badge_for`
- `_recommended_action_for`
- `_available_actions_for`
- `_access_summary_for`
- `_auth_summary_for`
- `_decorate_user`
- `_build_summary`

- [ ] **Step 4: user_service 구현**

다음 책임을 `user_service.py`로 이동한다.

- `_get_repo`, `_get_company_repo`
- `_validate_company`
- `_prepare_user_payload`
- `_get_user_or_404`
- 목록/상세/생성/수정/삭제 orchestration

- [ ] **Step 5: users route를 thin controller로 축소**

`routes/users.py`는 DTO 수신, query param 수신, service 호출만 남긴다.

- [ ] **Step 6: 테스트 통과 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_user_presenter.py tests/unit/test_users.py tests/unit/test_route_boundary.py -v
```
Expected: PASS

- [ ] **Step 7: 커밋**

```bash
git add services/platform/gateway/oneerp_gateway_app/services/user_service.py \
        services/platform/gateway/oneerp_gateway_app/services/user_presenter.py \
        services/platform/gateway/oneerp_gateway_app/routes/users.py \
        services/platform/gateway/tests/unit/test_user_presenter.py \
        services/platform/gateway/tests/unit/test_route_boundary.py
git commit -m "refactor(gateway): user workflow와 presenter를 분리"
```

---

## Task 5: Me 서비스 분리 + 전체 gateway 회귀

**Files:**
- Create: `services/platform/gateway/oneerp_gateway_app/services/me_service.py`
- Modify: `services/platform/gateway/oneerp_gateway_app/routes/me.py`
- Test: `services/platform/gateway/tests/unit/test_me_service.py`
- Test: `services/platform/gateway/tests/unit/test_route_boundary.py`

- [ ] **Step 1: 실패 테스트 작성**

`services/platform/gateway/tests/unit/test_route_boundary.py`에 추가:

```python
def test_me_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "me.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_route_boundary.py::test_me_route는_repository를_직접_사용하지_않는다 -v
```
Expected: FAIL

- [ ] **Step 3: me_service.py 구현**

`routes/me.py`의 tenant 조회, enabled modules 계산, user detail 조회를 `me_service.py`로 이동한다.

- [ ] **Step 4: me route 축소**

`routes/me.py`는 `get_me`, `update_me`에서 서비스 호출만 남긴다.

- [ ] **Step 5: 전체 gateway 검증**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit/test_auth_routes.py tests/unit/test_users.py tests/unit/test_me.py tests/unit/test_route_boundary.py tests/unit/test_dto_boundary.py tests/unit/test_token_service.py tests/unit/test_auth_service.py tests/unit/test_user_presenter.py tests/unit/test_me_service.py -v
uv run ruff check services/platform/gateway/oneerp_gateway_app services/platform/gateway/tests/unit
```
Expected: PASS

- [ ] **Step 6: gateway 전체 단위 테스트 재실행**

Run:
```bash
uv run --package oneerp-gateway --directory services/platform/gateway pytest tests/unit -q
```
Expected: PASS

- [ ] **Step 7: 최종 커밋**

```bash
git add services/platform/gateway/oneerp_gateway_app/services/me_service.py \
        services/platform/gateway/oneerp_gateway_app/routes/me.py \
        services/platform/gateway/tests/unit/test_me_service.py \
        services/platform/gateway/tests/unit/test_route_boundary.py \
        services/platform/gateway/tests/unit/test_dto_boundary.py
git commit -m "refactor(gateway): identity 경계를 auth users me로 정리"
```
