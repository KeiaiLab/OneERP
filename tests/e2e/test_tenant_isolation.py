"""E2E: 멀티테넌트 격리 검증 — 6개 시나리오.

실제 FerretDB에 테넌트 문서를 삽입하고,
TenantContextMiddleware + Repository 레벨의 격리 동작을 엔드투엔드로 검증한다.

시나리오:
1. 테넌트A 데이터를 테넌트B가 조회 → 404
2. 목록에 타 테넌트 데이터 미포함
3. 정지 테넌트 → 403
4. 만료 테넌트 → 403
5. 미허용 모듈 접근 → 403
6. super_admin 크로스테넌트 → 감사 로그 확인

구현 전략:
- 시나리오 1-2: Repository의 tenant_id 필터 검증 (DB 직접 삽입 + API 조회)
- 시나리오 3-6: TenantContextMiddleware 미들웨어 검증 (ASGI 클라이언트)
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from oneerp_core.auth import CurrentUser
from oneerp_core.middleware import clear_tenant_cache
from pymongo import MongoClient
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Generator

    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.e2e

# --- 환경 설정 ---
FERRETDB_URI = os.environ.get("FERRETDB_URI", "mongodb://localhost:27017")
E2E_DB_NAME = "oneerp_e2e_tenant_test"

# --- 인증 헤더 ---
HEADERS_A: dict[str, str] = {
    "X-Tenant-Id": "tenant-a",
    "X-User-Sub": "user-a",
    "X-User-Roles": "admin",
    "X-User-Tier": "regular",
    "X-User-Permissions": "item:create,item:read,item:list",
}

HEADERS_B: dict[str, str] = {
    "X-Tenant-Id": "tenant-b",
    "X-User-Sub": "user-b",
    "X-User-Roles": "admin",
    "X-User-Tier": "regular",
    "X-User-Permissions": "item:create,item:read,item:list",
}

HEADERS_ADMIN: dict[str, str] = {
    "X-Tenant-Id": "system",
    "X-User-Sub": "super-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "super_admin",
    "X-User-Permissions": "*:*",
}


# ---------------------------------------------------------------------------
# 헬퍼: 헤더 기반 사용자 주입 미들웨어
# ---------------------------------------------------------------------------
class _HeaderAuthMiddleware(BaseHTTPMiddleware):
    """X-* 헤더를 파싱하여 request.state.current_user를 설정하는 미들웨어.

    TenantContextMiddleware가 current_user를 참조하므로,
    E2E 테스트에서 실제 미들웨어 체인을 재현하기 위해 사용한다.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        user = _parse_user_from_headers(request)
        if user is not None:
            request.state.current_user = user
        return await call_next(request)


def _parse_user_from_headers(request: Any) -> CurrentUser | None:
    """요청 헤더에서 CurrentUser를 파싱한다."""
    tenant_id = request.headers.get("X-Tenant-Id", "")
    user_sub = request.headers.get("X-User-Sub", "")
    if not tenant_id or not user_sub:
        return None

    roles_str = request.headers.get("X-User-Roles", "")
    roles = tuple(r.strip() for r in roles_str.split(",") if r.strip()) if roles_str else ()
    user_tier = request.headers.get("X-User-Tier", "regular")
    perms_str = request.headers.get("X-User-Permissions", "")
    permissions = tuple(p.strip() for p in perms_str.split(",") if p.strip()) if perms_str else ()

    return CurrentUser(
        sub=user_sub,
        tenant_id=tenant_id,
        roles=roles,
        permissions=permissions,
        user_tier=user_tier,
        is_super_admin=user_tier == "super_admin",
    )


# ---------------------------------------------------------------------------
# 헬퍼: 테넌트 문서 생성
# ---------------------------------------------------------------------------
def _make_tenant_doc(
    *,
    tenant_id: str,
    is_active: bool = True,
    suspended_at: str | None = None,
    suspended_reason: str = "",
    contract_end: str | None = None,
    plan: str = "enterprise",
    allowed_modules: list[str] | None = None,
) -> dict[str, Any]:
    """FerretDB에 삽입할 테넌트 문서를 생성한다."""
    doc: dict[str, Any] = {
        "tenant_id": tenant_id,
        "name": f"테스트 테넌트 {tenant_id}",
        "is_active": is_active,
        "suspended_at": suspended_at,
        "suspended_reason": suspended_reason,
        "contract_end": contract_end,
        "plan": plan,
        "created_at": datetime.now(tz=UTC),
    }
    if allowed_modules is not None:
        doc["allowed_modules"] = allowed_modules
    return doc


# ---------------------------------------------------------------------------
# Fixture: FerretDB 연결 + 테넌트 준비
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def mongo_client() -> Generator[MongoClient]:
    """FerretDB 연결 — docker compose up -d 필요."""
    client: MongoClient = MongoClient(FERRETDB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception:
        pytest.skip("FerretDB에 연결할 수 없습니다. docker compose up -d를 실행하세요.")
    yield client
    client.close()


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """각 테스트 전에 테넌트 캐시를 초기화한다."""
    clear_tenant_cache()


@pytest.fixture(scope="module")
def db(mongo_client: MongoClient) -> Generator[Any]:
    """테스트용 DB를 반환하고 종료 시 정리한다."""
    test_db = mongo_client[E2E_DB_NAME]
    yield test_db
    mongo_client.drop_database(E2E_DB_NAME)


@pytest.fixture(scope="module")
def _setup_tenants(db: Any) -> None:
    """테스트용 테넌트 문서를 FerretDB에 삽입한다."""
    tenants = db["tenants"]
    # 기존 문서 정리
    tenants.delete_many({})

    yesterday = (datetime.now(tz=UTC) - timedelta(days=1)).date().isoformat()

    # 테넌트A: 정상 활성 (enterprise 플랜)
    tenants.insert_one(_make_tenant_doc(tenant_id="tenant-a", plan="enterprise"))

    # 테넌트B: 정상 활성 (enterprise 플랜)
    tenants.insert_one(_make_tenant_doc(tenant_id="tenant-b", plan="enterprise"))

    # 정지 테넌트
    tenants.insert_one(
        _make_tenant_doc(
            tenant_id="tenant-suspended",
            suspended_at="2026-01-01T00:00:00Z",
            suspended_reason="요금 미납",
        )
    )

    # 만료 테넌트
    tenants.insert_one(
        _make_tenant_doc(
            tenant_id="tenant-expired",
            contract_end=yesterday,
        )
    )

    # starter 플랜 테넌트 (hr 모듈 미포함)
    tenants.insert_one(
        _make_tenant_doc(
            tenant_id="tenant-starter",
            plan="starter",
        )
    )

    # system 테넌트 (super_admin 용)
    tenants.insert_one(_make_tenant_doc(tenant_id="system", plan="enterprise"))


@pytest.fixture(scope="module")
def _setup_env() -> None:
    """E2E 테스트용 환경변수를 설정한다."""
    os.environ["ONEERP_FERRETDB_URI"] = FERRETDB_URI
    os.environ["ONEERP_DATABASE_NAME"] = E2E_DB_NAME
    os.environ["ONEERP_DEBUG"] = "true"
    os.environ["ONEERP_SERVICE_NAME"] = "stock"

    # lru_cache 초기화 — 새 환경변수를 반영
    from oneerp_core.config import get_core_settings
    from oneerp_core.db import close_client

    get_core_settings.cache_clear()
    close_client()


@pytest.fixture(scope="module")
def stock_app(_setup_tenants: None, _setup_env: None) -> Any:
    """테넌트 격리 테스트용 Stock 서비스 앱을 생성한다.

    HeaderAuthMiddleware를 추가하여 X-* 헤더에서 사용자를 파싱하고
    request.state.current_user에 설정한다.
    """
    # stock 서비스 디렉토리를 import 경로에 추가
    stock_dir = str(Path(__file__).resolve().parent.parent.parent / "services" / "scm" / "stock")
    if stock_dir not in sys.path:
        sys.path.insert(0, stock_dir)

    app = import_module("oneerp_stock_app.main").app

    # HeaderAuthMiddleware 추가 (add_middleware는 역순 실행)
    # TenantContextMiddleware보다 먼저 실행되도록 나중에 등록
    app.add_middleware(_HeaderAuthMiddleware)

    return app


@pytest.fixture
async def client_a(stock_app: Any) -> AsyncIterator[httpx.AsyncClient]:
    """테넌트A 사용자의 httpx AsyncClient."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=stock_app),
        base_url="http://testserver",
        headers=HEADERS_A,
        timeout=10.0,
    ) as client:
        yield client


@pytest.fixture
async def client_b(stock_app: Any) -> AsyncIterator[httpx.AsyncClient]:
    """테넌트B 사용자의 httpx AsyncClient."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=stock_app),
        base_url="http://testserver",
        headers=HEADERS_B,
        timeout=10.0,
    ) as client:
        yield client


@pytest.fixture
async def client_admin(stock_app: Any) -> AsyncIterator[httpx.AsyncClient]:
    """super_admin의 httpx AsyncClient."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=stock_app),
        base_url="http://testserver",
        headers=HEADERS_ADMIN,
        timeout=10.0,
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# 시나리오 1: 테넌트A 데이터를 테넌트B가 조회 → 404
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("_setup_env")
class TestCrossTenantDataIsolation:
    """Repository 레벨의 테넌트 간 데이터 격리를 검증한다.

    DB에 서로 다른 tenant_id로 데이터를 직접 삽입한 뒤,
    Repository가 tenant_id 필터를 올바르게 적용하는지 확인한다.
    """

    def test_테넌트A_데이터_테넌트B_조회_404(self, db: Any) -> None:
        """테넌트A의 품목을 테넌트B의 Repository로 조회하면 None을 반환한다."""
        from oneerp_core.repository import Repository

        # 품목 컬렉션에 테넌트A/B 데이터 직접 삽입
        items = db["items"]
        item_id_a = "ITEM-TENANT-A-001"
        items.delete_many({"_id": {"$in": [item_id_a]}})
        items.insert_one(
            {
                "_id": item_id_a,
                "tenant_id": "tenant-a",
                "item_name": "테넌트A 전용 품목",
                "item_group": "완제품",
                "stock_uom": "EA",
                "docstatus": 0,
                "created_at": datetime.now(tz=UTC),
                "updated_at": datetime.now(tz=UTC),
            }
        )

        # 테넌트A Repository — 자기 데이터 조회 가능
        repo_a = Repository("items", tenant_id="tenant-a")
        doc = repo_a.find_by_id(item_id_a)
        assert doc is not None, "테넌트A가 자신의 데이터를 조회할 수 없음"
        assert doc["item_name"] == "테넌트A 전용 품목"

        # 테넌트B Repository — 테넌트A 데이터 조회 불가
        repo_b = Repository("items", tenant_id="tenant-b")
        doc = repo_b.find_by_id(item_id_a)
        assert doc is None, "테넌트B가 테넌트A의 데이터에 접근 가능"

    def test_목록에_타_테넌트_데이터_미포함(self, db: Any) -> None:
        """테넌트A 목록에 테넌트B의 데이터가 포함되지 않는다."""
        from oneerp_core.repository import Repository

        items = db["items"]
        item_id_a = "ITEM-LIST-A-001"
        item_id_b = "ITEM-LIST-B-001"

        # 기존 데이터 정리 후 삽입
        items.delete_many({"_id": {"$in": [item_id_a, item_id_b]}})
        now = datetime.now(tz=UTC)
        items.insert_one(
            {
                "_id": item_id_a,
                "tenant_id": "tenant-a",
                "item_name": "테넌트A 목록 품목",
                "item_group": "원자재",
                "docstatus": 0,
                "created_at": now,
                "updated_at": now,
            }
        )
        items.insert_one(
            {
                "_id": item_id_b,
                "tenant_id": "tenant-b",
                "item_name": "테넌트B 목록 품목",
                "item_group": "원자재",
                "docstatus": 0,
                "created_at": now,
                "updated_at": now,
            }
        )

        # 테넌트A 목록 — 자기 데이터만 포함
        repo_a = Repository("items", tenant_id="tenant-a")
        docs_a = repo_a.find_many()
        ids_a = [d["_id"] for d in docs_a]
        assert item_id_a in ids_a, "테넌트A 자신의 품목이 목록에 없음"
        assert item_id_b not in ids_a, f"테넌트B의 품목({item_id_b})이 테넌트A 목록에 포함됨"

        # 테넌트B 목록 — 자기 데이터만 포함
        repo_b = Repository("items", tenant_id="tenant-b")
        docs_b = repo_b.find_many()
        ids_b = [d["_id"] for d in docs_b]
        assert item_id_b in ids_b, "테넌트B 자신의 품목이 목록에 없음"
        assert item_id_a not in ids_b, f"테넌트A의 품목({item_id_a})이 테넌트B 목록에 포함됨"


# ---------------------------------------------------------------------------
# 시나리오 3: 정지 테넌트 → 403
# ---------------------------------------------------------------------------
class TestSuspendedTenant:
    """정지된 테넌트의 접근 차단을 검증한다."""

    @pytest.mark.anyio
    async def test_정지_테넌트_403(self, stock_app: Any) -> None:
        """정지된 테넌트의 요청은 403을 반환한다."""
        headers_suspended = {
            "X-Tenant-Id": "tenant-suspended",
            "X-User-Sub": "user-suspended",
            "X-User-Roles": "admin",
            "X-User-Tier": "regular",
            "X-User-Permissions": "item:read,item:list",
        }

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=stock_app),
            base_url="http://testserver",
            headers=headers_suspended,
            timeout=10.0,
        ) as client:
            resp = await client.get("/api/v1/items")
            assert resp.status_code == 403, f"정지 테넌트가 접근 가능: {resp.text}"
            detail = resp.json()["detail"]
            assert "정지" in detail
            assert "요금 미납" in detail


# ---------------------------------------------------------------------------
# 시나리오 4: 만료 테넌트 → 403
# ---------------------------------------------------------------------------
class TestExpiredTenant:
    """만료된 테넌트의 접근 차단을 검증한다."""

    @pytest.mark.anyio
    async def test_만료_테넌트_403(self, stock_app: Any) -> None:
        """계약 만료된 테넌트의 요청은 403을 반환한다."""
        headers_expired = {
            "X-Tenant-Id": "tenant-expired",
            "X-User-Sub": "user-expired",
            "X-User-Roles": "admin",
            "X-User-Tier": "regular",
            "X-User-Permissions": "item:read,item:list",
        }

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=stock_app),
            base_url="http://testserver",
            headers=headers_expired,
            timeout=10.0,
        ) as client:
            resp = await client.get("/api/v1/items")
            assert resp.status_code == 403, f"만료 테넌트가 접근 가능: {resp.text}"
            assert "만료" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 시나리오 5: 미허용 모듈 접근 → 403
# ---------------------------------------------------------------------------
class TestModuleAccessRestriction:
    """플랜별 모듈 접근 제한을 검증한다."""

    @pytest.mark.anyio
    async def test_미허용_모듈_접근_403(self, stock_app: Any) -> None:
        """starter 플랜 테넌트가 hr 모듈(employees)에 접근하면 403을 반환한다.

        미들웨어가 URL 경로 기반으로 모듈을 판별하므로,
        stock 앱에 임시 employees 라우트를 등록하여 테스트한다.
        starter 플랜에는 hr 모듈이 포함되지 않는다.
        """
        from fastapi import APIRouter
        from fastapi.responses import JSONResponse as FastAPIJSONResponse

        # 임시 employees 라우트 등록 (모듈 매핑 테스트용)
        _temp_router = APIRouter()

        @_temp_router.get("/api/v1/employees")
        async def _temp_employees() -> FastAPIJSONResponse:
            return FastAPIJSONResponse({"data": []})

        stock_app.include_router(_temp_router)

        headers_starter = {
            "X-Tenant-Id": "tenant-starter",
            "X-User-Sub": "user-starter",
            "X-User-Roles": "admin",
            "X-User-Tier": "regular",
            "X-User-Permissions": "employee:read",
        }

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=stock_app),
            base_url="http://testserver",
            headers=headers_starter,
            timeout=10.0,
        ) as client:
            resp = await client.get("/api/v1/employees")
            assert resp.status_code == 403, f"미허용 모듈 접근 가능: {resp.text}"
            detail = resp.json()["detail"]
            assert "hr" in detail


# ---------------------------------------------------------------------------
# 시나리오 6: super_admin 크로스테넌트 → 감사 로그 확인
# ---------------------------------------------------------------------------
class TestSuperAdminCrossTenant:
    """super_admin의 크로스테넌트 접근과 감사 로그를 검증한다."""

    @pytest.mark.anyio
    async def test_super_admin_크로스테넌트_감사_로그(
        self,
        client_admin: httpx.AsyncClient,
        db: Any,
    ) -> None:
        """super_admin이 API에 접근하면 감사 로그가 기록된다."""
        # 감사 로그 컬렉션 초기화
        db["audit_events"].delete_many({"actor": "super-admin"})

        # super_admin으로 API 접근
        resp = await client_admin.get("/api/v1/items")
        assert resp.status_code == 200, f"super_admin 접근 실패: {resp.text}"

        # 감사 로그 확인
        audit_events = list(
            db["audit_events"].find({"actor": "super-admin", "action": "super_admin_access"})
        )
        assert len(audit_events) >= 1, "super_admin 감사 로그가 기록되지 않음"

        # 감사 로그 내용 검증
        event = audit_events[-1]
        assert event["actor"] == "super-admin"
        assert event["action"] == "super_admin_access"
        assert event["tenant_id"] == "system"
        assert "/api/v1/items" in event["resource"]
        assert event.get("details", {}).get("is_super_admin") is True
