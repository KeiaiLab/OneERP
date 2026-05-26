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
import sys
import time
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from pymongo import MongoClient

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


def _start_service(name: str, port: int) -> subprocess.Popen:
    """서비스를 subprocess로 기동한다."""
    service_dir = str(Path(ROOT_DIR) / "services" / name)
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
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    return subprocess.Popen(  # noqa: S603
        cmd,
        cwd=service_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture(scope="session")
def services(_clean_db: None) -> Generator[dict[str, str]]:
    """15개 서비스를 모두 기동하고 base URL 딕셔너리를 반환한다.

    이미 포트가 점유된 서비스는 기존 인스턴스를 재사용한다.
    """
    processes: list[subprocess.Popen] = []
    urls: dict[str, str] = {}

    for name, port in SERVICE_PORTS.items():
        urls[name] = f"http://127.0.0.1:{port}"
        if _port_is_open(port):
            logger.info("서비스 '%s' 포트 %d 이미 기동 중 — 재사용", name, port)
        else:
            proc = _start_service(name, port)
            processes.append(proc)

    # 모든 서비스가 준비될 때까지 대기
    for name, port in SERVICE_PORTS.items():
        try:
            _wait_for_service(port, timeout=30.0)
        except TimeoutError:
            for p in processes:
                p.terminate()
            pytest.fail(f"서비스 '{name}'이 포트 {port}에서 기동되지 않았습니다")

    yield urls

    # 정리: 직접 기동한 프로세스만 종료 (외부 기동 서비스는 건드리지 않음)
    for proc in processes:
        proc.send_signal(signal.SIGTERM)
    for proc in processes:
        proc.wait(timeout=10)


@pytest.fixture(scope="session")
def gateway_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Gateway 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["gateway"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def selling_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Selling 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["selling"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def buying_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Buying 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["buying"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def stock_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Stock 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["stock"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def accounting_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Accounting 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["accounting"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def hr_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """HR 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["hr"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def payroll_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Payroll 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["payroll"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def expenses_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Expenses 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["expenses"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def crm_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """CRM 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["crm"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def assets_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Assets 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["assets"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def projects_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Projects 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["projects"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def quality_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Quality 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["quality"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def analytics_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Analytics 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["analytics"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def manufacturing_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """Manufacturing 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["manufacturing"], timeout=10.0) as client:
        yield client


@pytest.fixture(scope="session")
def rpa_client(services: dict[str, str]) -> Generator[httpx.Client]:
    """RPA 서비스 httpx 클라이언트."""
    with httpx.Client(base_url=services["rpa"], timeout=10.0) as client:
        yield client
