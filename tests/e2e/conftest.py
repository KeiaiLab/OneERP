"""E2E 테스트 공통 fixture.

각 서비스를 subprocess로 기동하고 httpx 클라이언트를 제공한다.
FerretDB는 docker compose로 사전 기동 필요.
"""

from __future__ import annotations

import logging
import os
import signal
import socket
import subprocess
import time
import tomllib
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx
import pytest
from pymongo import MongoClient

from tests.e2e.helpers.api_client import HEADERS

logger = logging.getLogger(__name__)


def wait_for_condition(
    check_fn,
    *,
    timeout: float = 10.0,
    interval: float = 0.5,
    description: str = "조건 충족 대기",
):
    """조건 함수가 truthy 값을 반환할 때까지 폴링 대기한다.

    check_fn이 truthy 값을 반환하면 해당 값을 즉시 반환한다.
    timeout 초 내에 조건이 충족되지 않으면 TimeoutError를 발생시킨다.
    """
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            result = check_fn()
            if result:
                return result
        except Exception as e:
            last_error = e
        time.sleep(interval)
    msg = f"{description}: {timeout}초 내 조건 미충족"
    if last_error:
        msg += f" (마지막 에러: {last_error})"
    raise TimeoutError(msg)


# --- 환경 설정 ---
FERRETDB_URI = os.environ.get("FERRETDB_URI", "mongodb://localhost:27017")
E2E_DB_NAME = "oneerp_e2e_test"
ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)

# 서비스별 포트 매핑
SERVICE_PORTS: dict[str, int] = {
    "gateway": 8001,
    "selling": 8002,
    "buying": 8003,
    "stock": 8004,
    "accounting": 8005,
    "hr": 8006,
    "payroll": 8007,
    "expenses": 8008,
    "crm": 8009,
    "assets": 8010,
    "projects": 8011,
    "quality": 8012,
    "analytics": 8013,
    "manufacturing": 8014,
    "rpa": 8015,
    "knowledge": 8016,
    "documents": 8017,
}

SERVICE_DIRS: dict[str, str] = {
    "gateway": "services/platform/gateway",
    "selling": "services/sales/selling",
    "buying": "services/scm/buying",
    "stock": "services/scm/stock",
    "accounting": "services/finance/accounting",
    "hr": "services/hr/hr",
    "payroll": "services/finance/payroll",
    "expenses": "services/finance/expenses",
    "crm": "services/sales/crm",
    "assets": "services/assets/assets",
    "projects": "services/collab/projects",
    "quality": "services/scm/qm",
    "analytics": "services/platform/analytics",
    "manufacturing": "services/scm/manufacturing",
    "rpa": "services/platform/rpa",
    "knowledge": "services/collab/knowledge",
    "documents": "services/collab/documents",
}

# 서비스별 uvicorn 앱 모듈 — 기본은 oneerp_{name}_app.main:app
SERVICE_APP_MODULES: dict[str, str] = {
    "quality": "oneerp_qm_app.main:app",
}


def _port_is_open(port: int, *, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    """포트가 열려 있는지 확인한다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def _wait_for_service(port: int, *, timeout: float = 30.0) -> None:
    """서비스가 응답할 때까지 대기한다."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_is_open(port):
            return
        time.sleep(0.3)
    msg = f"서비스가 포트 {port}에서 {timeout}초 내에 응답하지 않았습니다"
    raise TimeoutError(msg)


def _make_service_client(base_url: str) -> httpx.Client:
    """E2E 서비스 기본 인증 헤더를 포함한 httpx 클라이언트를 생성한다."""
    return httpx.Client(base_url=base_url, timeout=10.0, headers=HEADERS.copy())


@pytest.fixture(scope="session", autouse=True)
def _ensure_nats_stream() -> None:
    """ONEERP JetStream 이 없으면 subjects=['oneerp.>'] 로 생성한다.

    Phase 1 이벤트 체인 회귀 중 확인된 근본 원인: 스트림 미등록 시
    NatsPublisher 발행이 silently 실패해 OutboxPoller→소비자 경로가 끊긴다.
    테스트 인프라에서 자동 보장한다(프로덕션은 scripts/dev/init-nats-streams.sh 사용).
    """
    import asyncio

    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    try:
        import nats
        from nats.js.api import StorageType, StreamConfig
    except ImportError:
        logger.warning("nats-py 미설치 — 스트림 초기화 스킵")
        return

    async def _ensure() -> None:
        nc = await nats.connect(nats_url)
        js = nc.jetstream()
        try:
            await js.stream_info("ONEERP")
        except Exception:
            await js.add_stream(
                StreamConfig(
                    name="ONEERP",
                    subjects=["oneerp.>"],
                    storage=StorageType.FILE,
                )
            )
            logger.info("ONEERP JetStream 생성 완료")
        await nc.close()

    try:
        asyncio.run(_ensure())
    except Exception as exc:
        logger.warning("NATS 스트림 초기화 실패 (무시하고 진행): %s", exc)


@pytest.fixture(scope="session")
def mongo_client() -> Generator[MongoClient]:
    """FerretDB 연결 — docker compose up -d 필요."""
    client: MongoClient = MongoClient(FERRETDB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception:
        pytest.skip("FerretDB에 연결할 수 없습니다. docker compose up -d를 실행하세요.")
    yield client
    client.close()


@pytest.fixture(scope="session")
def _clean_db(mongo_client: MongoClient) -> Generator[None]:
    """테스트 DB를 세션 시작/종료 시 정리한다."""
    mongo_client.drop_database(E2E_DB_NAME)
    yield
    mongo_client.drop_database(E2E_DB_NAME)


@pytest.fixture(scope="session")
def seeded_credentials(mongo_client: MongoClient, _clean_db: None) -> dict[str, Any]:
    """E2E 테스트용 기본 테넌트/관리자 사용자를 시드한다.

    반환값은 로그인에 그대로 사용할 수 있는 {tenant_id, username, password, roles}.
    """
    from tests.e2e.helpers.seed import seed_minimal_auth

    return seed_minimal_auth(mongo_client, E2E_DB_NAME)


def _start_service(name: str, port: int) -> subprocess.Popen:
    """서비스를 subprocess로 기동한다.

    stderr 는 `artifacts/e2e-logs/<name>-stderr.log` 로 redirect 한다.
    이전엔 DEVNULL 이었으나 500 에러 디버깅이 불가능해 파일 로그로 전환
    (Ralph-Loop iter 2, 2026-04-16). stdout 은 여전히 DEVNULL.
    """
    relative_dir = SERVICE_DIRS.get(name, f"services/{name}")
    service_dir = Path(ROOT_DIR) / relative_dir
    # 기본 앱 모듈 — SERVICE_APP_MODULES에 없으면 oneerp_{name}_app.main:app 규칙 적용
    app_module = SERVICE_APP_MODULES.get(name, f"oneerp_{name}_app.main:app")
    package_name = tomllib.loads((service_dir / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["name"]
    env = {
        **os.environ,
        "ONEERP_FERRETDB_URI": FERRETDB_URI,
        "ONEERP_DATABASE_NAME": E2E_DB_NAME,
        "ONEERP_DEBUG": "true",
        "ONEERP_NATS_URL": os.environ.get("NATS_URL", "nats://localhost:4222"),
        "ONEERP_VALKEY_URL": os.environ.get("VALKEY_URL", "redis://localhost:6379"),
        "ONEERP_OUTBOX_POLL_INTERVAL": "1",
    }
    cmd = [
        "uv",
        "run",
        "--package",
        package_name,
        "--directory",
        str(service_dir),
        "uvicorn",
        app_module,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    log_dir = Path(ROOT_DIR) / "artifacts" / "e2e-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = (log_dir / f"{name}-stderr.log").open("ab")
    return subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(service_dir),
        env=env,
        stdout=log_file,
        stderr=log_file,
    )


def _start_services_subset(
    names: list[str],
    *,
    wait_timeout: float = 90.0,
) -> tuple[dict[str, str], list[subprocess.Popen]]:
    """주어진 서비스만 기동하고 (urls, processes) 를 반환한다.

    이미 포트가 열린 서비스는 기존 인스턴스를 재사용한다.
    """
    processes: list[subprocess.Popen] = []
    urls: dict[str, str] = {}
    for name in names:
        port = SERVICE_PORTS[name]
        urls[name] = f"http://127.0.0.1:{port}"
        if _port_is_open(port):
            logger.info("서비스 '%s' 포트 %d 이미 기동 중 — 재사용", name, port)
        else:
            processes.append(_start_service(name, port))

    for name in names:
        port = SERVICE_PORTS[name]
        try:
            _wait_for_service(port, timeout=wait_timeout)
        except TimeoutError:
            for p in processes:
                p.terminate()
            pytest.fail(f"서비스 '{name}'이 포트 {port}에서 기동되지 않았습니다")
    return urls, processes


def _stop_processes(processes: list[subprocess.Popen]) -> None:
    """기동했던 프로세스를 안전하게 종료한다."""
    for proc in processes:
        proc.send_signal(signal.SIGTERM)
    for proc in processes:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def services(_clean_db: None) -> Generator[dict[str, str]]:
    """전체 서비스를 기동하고 base URL 딕셔너리를 반환한다 (역호환)."""
    urls, processes = _start_services_subset(list(SERVICE_PORTS.keys()))
    try:
        yield urls
    finally:
        _stop_processes(processes)


# Order-to-Cash 플로우에 필요한 최소 서비스 — gateway(auth) + selling + stock + accounting
OTC_SERVICES = ["gateway", "selling", "stock", "accounting"]


@pytest.fixture(scope="session")
def otc_services(_clean_db: None) -> Generator[dict[str, str]]:
    """Order-to-Cash 최소 서비스만 기동한다 — 전체 기동보다 훨씬 빠름."""
    urls, processes = _start_services_subset(OTC_SERVICES)
    try:
        yield urls
    finally:
        _stop_processes(processes)


@pytest.fixture
def otc_auth_session(
    otc_services: dict[str, str],
    seeded_credentials: dict[str, Any],
) -> Generator[Any]:
    """OTC 플로우용 로그인 세션 — 테스트 시작에 login, 종료에 logout을 보장한다."""
    from tests.e2e.helpers.auth import auth_session

    with auth_session(
        otc_services["gateway"],
        tenant_id=seeded_credentials["tenant_id"],
        username=seeded_credentials["username"],
        password=seeded_credentials["password"],
    ) as session:
        yield session


@pytest.fixture(scope="session")
def otc_selling_client(otc_services: dict[str, str]) -> Generator[httpx.Client]:
    """OTC 최소 기동에서의 Selling 서비스 httpx 클라이언트."""
    with _make_service_client(otc_services["selling"]) as client:
        yield client


@pytest.fixture(scope="session")
def otc_stock_client(otc_services: dict[str, str]) -> Generator[httpx.Client]:
    """OTC 최소 기동에서의 Stock 서비스 httpx 클라이언트."""
    with _make_service_client(otc_services["stock"]) as client:
        yield client


@pytest.fixture(scope="session")
def otc_accounting_client(otc_services: dict[str, str]) -> Generator[httpx.Client]:
    """OTC 최소 기동에서의 Accounting 서비스 httpx 클라이언트."""
    with _make_service_client(otc_services["accounting"]) as client:
        yield client


@pytest.fixture(scope="session")
def gateway_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Gateway 서비스 httpx 클라이언트."""
    with _make_service_client(services["gateway"]) as client:
        yield client


@pytest.fixture(scope="session")
def selling_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Selling 서비스 httpx 클라이언트."""
    with _make_service_client(services["selling"]) as client:
        yield client


@pytest.fixture(scope="session")
def buying_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Buying 서비스 httpx 클라이언트."""
    with _make_service_client(services["buying"]) as client:
        yield client


@pytest.fixture(scope="session")
def stock_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Stock 서비스 httpx 클라이언트."""
    with _make_service_client(services["stock"]) as client:
        yield client


@pytest.fixture(scope="session")
def accounting_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Accounting 서비스 httpx 클라이언트."""
    with _make_service_client(services["accounting"]) as client:
        yield client


@pytest.fixture(scope="session")
def hr_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """HR 서비스 httpx 클라이언트."""
    with _make_service_client(services["hr"]) as client:
        yield client


@pytest.fixture(scope="session")
def payroll_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Payroll 서비스 httpx 클라이언트."""
    with _make_service_client(services["payroll"]) as client:
        yield client


@pytest.fixture(scope="session")
def expenses_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Expenses 서비스 httpx 클라이언트."""
    with _make_service_client(services["expenses"]) as client:
        yield client


@pytest.fixture(scope="session")
def crm_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """CRM 서비스 httpx 클라이언트."""
    with _make_service_client(services["crm"]) as client:
        yield client


@pytest.fixture(scope="session")
def knowledge_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Knowledge 서비스 httpx 클라이언트."""
    with _make_service_client(services["knowledge"]) as client:
        yield client


@pytest.fixture(scope="session")
def documents_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Documents 서비스 httpx 클라이언트."""
    with _make_service_client(services["documents"]) as client:
        yield client


@pytest.fixture(scope="session")
def assets_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Assets 서비스 httpx 클라이언트."""
    with _make_service_client(services["assets"]) as client:
        yield client


@pytest.fixture(scope="session")
def projects_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Projects 서비스 httpx 클라이언트."""
    with _make_service_client(services["projects"]) as client:
        yield client


@pytest.fixture(scope="session")
def quality_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Quality 서비스 httpx 클라이언트."""
    with _make_service_client(services["quality"]) as client:
        yield client


@pytest.fixture(scope="session")
def analytics_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Analytics 서비스 httpx 클라이언트."""
    with _make_service_client(services["analytics"]) as client:
        yield client


@pytest.fixture(scope="session")
def manufacturing_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Manufacturing 서비스 httpx 클라이언트."""
    with _make_service_client(services["manufacturing"]) as client:
        yield client


@pytest.fixture(scope="session")
def rpa_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """RPA 서비스 httpx 클라이언트."""
    with _make_service_client(services["rpa"]) as client:
        yield client
