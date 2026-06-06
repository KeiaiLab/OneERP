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
    assert "core" in gateway.compose_profiles
    assert gateway.local_debug_port == 8001
    assert gateway.k8s_enabled is True
    assert web.runtime == "node"
    assert web.route_prefix == "/"
    assert web.local_debug_port == 3000


def test_compose_렌더링은_공유_env와_프로파일을_반영한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_compose")
    generator_module = _load_module("scripts/deploy/generator.py", "deploy_generator_compose")

    services = catalog_module.load_service_catalog(ROOT)
    release = catalog_module.load_release_manifest(ROOT)
    rendered = generator_module.render_compose_yaml(services, release)
    compose_doc = yaml.safe_load(rendered)

    gateway = compose_doc["services"]["gateway"]
    web = compose_doc["services"]["web"]
    postgres = compose_doc["services"]["postgres"]
    ferretdb = compose_doc["services"]["ferretdb"]
    nats = compose_doc["services"]["nats"]

    assert gateway["profiles"] == ["core", "business", "advanced", "full"]
    assert gateway["depends_on"]["ferretdb"]["condition"] == "service_started"
    assert gateway["environment"]["ONEERP_SERVICE_NAME"] == "gateway"
    assert gateway["environment"]["ONEERP_FERRETDB_URI"] == "mongodb://ferretdb:27017"
    assert web["profiles"] == ["core", "business", "advanced", "full"]
    assert web["environment"]["ONEERP_GATEWAY_URL"] == "http://gateway:8000"
    assert web["depends_on"]["gateway"]["condition"] == "service_started"
    assert postgres["image"] == "ghcr.io/ferretdb/postgres-documentdb:17-0.107.0-ferretdb-2.7.0"
    assert postgres["environment"]["POSTGRES_USER"] == "ferret"
    assert "mongosh" not in str(ferretdb.get("healthcheck", {}))
    assert "-m" in nats["command"]
    assert "8222" in nats["command"]


def test_서비스_스캐폴드_렌더링은_chart와_dockerfile_템플릿을_제공한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_scaffold")
    generator_module = _load_module("scripts/deploy/generator.py", "deploy_generator_scaffold")

    services = catalog_module.load_service_catalog(ROOT)
    gateway = services["gateway"]

    dockerfile = generator_module.render_service_dockerfile(gateway)
    chart_yaml = generator_module.render_chart_yaml(gateway)
    values_prod = generator_module.render_values_prod_yaml(gateway, "latest")

    assert "uv sync --frozen --package oneerp-gateway --no-dev" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in dockerfile
    assert "name: oneerp-gateway" in chart_yaml
    assert 'repository: "file://../oneerp-common"' in chart_yaml
    assert "rewritePath: /" in values_prod
    assert "/api/gateway/" in values_prod


def test_로컬_compose_override는_full_프로파일_서비스_포트를_모두_노출한다() -> None:
    catalog_module = _load_module("scripts/deploy/catalog.py", "deploy_catalog_local")
    generator_module = _load_module("scripts/deploy/generator.py", "deploy_generator_local")

    services = catalog_module.load_service_catalog(ROOT)
    release = catalog_module.load_release_manifest(ROOT)
    rendered = generator_module.render_local_compose_yaml(services, release)
    compose_doc = yaml.safe_load(rendered)

    full_services = [
        service
        for service in services.values()
        if service.compose_enabled and "full" in service.compose_profiles
    ]

    for service in full_services:
        service_doc = compose_doc["services"][service.name]
        assert service_doc["ports"] == [f"{service.local_debug_port}:{service.container_port}"]

    assert compose_doc["services"]["gateway"]["environment"]["ONEERP_DEBUG"] == "true"
    assert compose_doc["services"]["web"]["build"]["dockerfile"] == "apps/web/Dockerfile"


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
    assert "uv run python" in init_script
    assert "ONEERP_DLQ" not in init_script
