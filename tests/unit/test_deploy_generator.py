from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_module(relative_path: str, module_name: str):
    module_path = ROOT / relative_path
    if not module_path.exists():
        pytest.fail(f"모듈이 없습니다: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_배포_카탈로그는_공통_릴리즈_대상_서비스를_정의한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog")

    services = catalog_module.load_service_catalog(ROOT)
    release = catalog_module.load_release_manifest(ROOT)

    assert "gateway" in services
    assert "web" in services
    assert release.version
    assert set(release.services) == set(services)

    gateway = services["gateway"]
    web = services["web"]

    assert gateway.runtime == "python"
    assert gateway.route_prefix == "/api/gateway/"
    assert gateway.local_debug_port == 8001
    assert gateway.k8s_enabled is True
    assert web.runtime == "node"
    assert web.route_prefix == "/"
    assert web.local_debug_port == 3000


def test_plane_카탈로그는_6_plane을_로드한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_plane")

    planes = catalog_module.load_plane_catalog(ROOT)

    assert set(planes) == {"api", "realtime", "worker", "scheduler", "edge", "extension"}
    edge = planes["edge"]
    api = planes["api"]
    worker = planes["worker"]

    # 모든 plane 은 internal-only — 외부 진입은 edge-router(Caddy) 가 단일 담당.
    assert edge.host_port is None
    assert api.host_port is None
    assert worker.host_port is None

    # 공통 infra 의존성과 환경변수 상속.
    assert "nats" in api.infra_dependencies
    assert "ferretdb" in api.infra_dependencies
    assert api.environment["ONEERP_FERRETDB_URI"] == "mongodb://ferretdb:27017"

    # 프로파일.
    assert "plane" in api.compose_profiles


def test_compose_렌더링은_hostname_기반_plane_통신을_구성한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_compose")
    generator_module = _load_module("scripts/deploy/generator.py", "deploy_generator_compose")

    planes = catalog_module.load_plane_catalog(ROOT)
    services = catalog_module.load_service_catalog(ROOT)
    release = catalog_module.load_release_manifest(ROOT)
    rendered = generator_module.render_compose_yaml(planes, services, release)
    compose_doc = yaml.safe_load(rendered)

    service_names = set(compose_doc["services"])
    # 인프라 4개 + 6 plane + web + edge-router.
    assert {"postgres", "ferretdb", "valkey", "nats"} <= service_names
    assert {
        "api-plane",
        "realtime-plane",
        "worker-plane",
        "scheduler-plane",
        "edge-plane",
        "extension-plane",
    } <= service_names
    assert {"web", "edge-router"} <= service_names

    api_plane = compose_doc["services"]["api-plane"]
    edge_plane = compose_doc["services"]["edge-plane"]
    worker_plane = compose_doc["services"]["worker-plane"]
    postgres = compose_doc["services"]["postgres"]
    web = compose_doc["services"]["web"]
    edge_router = compose_doc["services"]["edge-router"]

    # hostname 설정으로 plane 간 DNS 주소 확정.
    assert api_plane["hostname"] == "api-plane"
    assert edge_plane["hostname"] == "edge-plane"

    # 모든 plane 과 web 은 외부 호스트 포트 없음 — edge-router 만 진입.
    assert "ports" not in api_plane
    assert "ports" not in worker_plane
    assert "ports" not in edge_plane
    assert "ports" not in web
    assert edge_router["ports"] == ["8080:80"]
    assert edge_router["image"].startswith("caddy:")

    # 인프라 포트도 expose 만(외부 노출 금지, hostname 통신).
    assert "ports" not in postgres
    assert postgres["expose"] == ["5432"]

    # plane 간 통신 URL 이 hostname:containerPort 로 주입.
    env = api_plane["environment"]
    assert env["ONEERP_PLANE_EDGE_URL"] == "http://edge-plane:8000"
    assert env["ONEERP_PLANE_WORKER_URL"] == "http://worker-plane:8000"
    assert env["ONEERP_PLANE_NAME"] == "api"

    # 인프라 의존성 (compose v2.20+ healthy 조건).
    assert api_plane["depends_on"]["nats"]["condition"] == "service_healthy"
    assert api_plane["depends_on"]["ferretdb"]["condition"] == "service_started"

    # web — 내부 expose 만, edge-plane healthy 대기.
    assert web["expose"] == ["3000"]
    assert web["environment"]["NEXT_PUBLIC_API_BASE_URL"] == "http://edge-plane:8000"
    assert web["depends_on"]["edge-plane"]["condition"] == "service_healthy"

    # edge-router — web/edge-plane healthy 대기.
    assert edge_router["depends_on"]["edge-plane"]["condition"] == "service_healthy"
    assert edge_router["depends_on"]["web"]["condition"] == "service_healthy"


def test_compose_렌더링은_로컬기본값으로_pull대신_build를_사용한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_compose_pull_policy")
    generator_module = _load_module(
        "scripts/deploy/generator.py", "deploy_generator_compose_pull_policy"
    )

    planes = catalog_module.load_plane_catalog(ROOT)
    services = catalog_module.load_service_catalog(ROOT)
    release = catalog_module.load_release_manifest(ROOT)
    rendered = generator_module.render_compose_yaml(planes, services, release)
    compose_doc = yaml.safe_load(rendered)

    api_plane = compose_doc["services"]["api-plane"]
    web = compose_doc["services"]["web"]
    postgres = compose_doc["services"]["postgres"]
    nats = compose_doc["services"]["nats"]

    assert api_plane["pull_policy"] == "${ONEERP_COMPOSE_PULL_POLICY:-build}"
    assert web["pull_policy"] == "${ONEERP_COMPOSE_PULL_POLICY:-build}"
    assert "pull_policy" not in postgres
    assert "pull_policy" not in nats


def test_caddyfile_렌더링은_api와_web을_분기한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_caddy")
    generator_module = _load_module("scripts/deploy/generator.py", "deploy_generator_caddy")

    planes = catalog_module.load_plane_catalog(ROOT)
    rendered = generator_module.render_caddyfile(planes)

    assert "GENERATED FILE" in rendered
    assert "reverse_proxy edge-plane:8000" in rendered
    assert "reverse_proxy web:3000" in rendered
    assert "handle /api/*" in rendered


def test_applicationset_렌더링은_k8s_활성_서비스만_포함한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_appset")
    generator_module = _load_module("scripts/deploy/generator.py", "deploy_generator_appset")

    services = catalog_module.load_service_catalog(ROOT)
    release = catalog_module.load_release_manifest(ROOT)
    rendered = generator_module.render_applicationset_yaml(services, release)
    appset_doc = yaml.safe_load(rendered)

    elements = appset_doc["spec"]["generators"][0]["list"]["elements"]
    listed_services = [item["service"] for item in elements]
    target_revision = appset_doc["spec"]["template"]["spec"]["source"]["targetRevision"]

    assert "gateway" in listed_services
    assert "web" in listed_services
    assert target_revision == release.version
    assert target_revision != "main"
    assert sorted(listed_services) == sorted(
        [service.name for service in services.values() if service.k8s_enabled],
    )


def test_서비스_스캐폴드는_helm_chart_템플릿만_생성한다() -> None:
    """ADR-0014 이후 도메인 Dockerfile 자동 생성은 중단 — Helm chart 만 스캐폴드."""
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_scaffold")
    generator_module = _load_module("scripts/deploy/generator.py", "deploy_generator_scaffold")

    services = catalog_module.load_service_catalog(ROOT)
    gateway = services["gateway"]

    chart_yaml = generator_module.render_chart_yaml(gateway)
    values_prod = generator_module.render_values_prod_yaml(gateway, "latest")

    assert "name: oneerp-gateway" in chart_yaml
    assert 'repository: "file://../oneerp-common"' in chart_yaml
    assert "rewritePath: /" in values_prod
    assert "/api/gateway/" in values_prod


def test_로컬_seed_계약은_demo_demo1234_로그인을_만든다() -> None:
    seed_script = (ROOT / "scripts" / "dev" / "seed-data.sh").read_text(encoding="utf-8")

    assert "demo1234" in seed_script
    assert "hashlib.sha256" in seed_script
    assert '"username": "demo"' in seed_script
    assert "mongosh" not in seed_script
    assert "uv run python" in seed_script
    assert "$2b$12$LJ3lKzS1kV9Xk.KZrOxzqu0wFb9WhDo7Bt9fGbYJyL9VKf5z5G7S." not in seed_script


def test_nats_초기화_스크립트는_로컬_nats_cli에_의존하지_않는다() -> None:
    init_script = (ROOT / "scripts" / "dev" / "init-nats-streams.sh").read_text(encoding="utf-8")

    assert "nats --server" not in init_script
    assert "docker compose exec" in init_script
    assert "ONEERP_DLQ" not in init_script
