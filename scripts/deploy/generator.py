"""배포 카탈로그 기반 산출물 생성기.

ADR-0014 이후 docker-compose 렌더링 단위는 6 Runtime Plane 이다.
Helm 차트 산출물은 여전히 48 도메인 단위(services.yaml) 로 생성한다.
배포 reconcile 은 Flux 가 직접 deploy/charts 를 watch 한다 (RFC-0048, ArgoCD ApplicationSet 폐기).
"""

from __future__ import annotations

import os
from textwrap import dedent
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.deploy.catalog import PlaneSpec, ReleaseManifest, ServiceSpec


COMPOSE_BUILD_PULL_POLICY = "${ONEERP_COMPOSE_PULL_POLICY:-build}"


def _dump_yaml(document: dict[str, Any]) -> str:
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False)


def _compose_plane_service_name(plane: PlaneSpec) -> str:
    """compose service 이름 — 다른 컨테이너에서 이 hostname 으로 접근한다."""
    return f"{plane.name}-plane"


def _plane_env_for_compose(plane: PlaneSpec, planes: dict[str, PlaneSpec]) -> dict[str, str]:
    env = dict(plane.environment)
    env["ONEERP_SERVICE_NAME"] = f"plane-{plane.name}"
    env["ONEERP_PLANE_NAME"] = plane.name
    # 동일 네트워크 내 plane 간 통신용 URL (hostname:container_port).
    for peer in planes.values():
        key = f"ONEERP_PLANE_{peer.name.upper().replace('-', '_')}_URL"
        env[key] = f"http://{_compose_plane_service_name(peer)}:{peer.container_port}"
    return env


def _compose_plane_definition(
    plane: PlaneSpec, release: ReleaseManifest, planes: dict[str, PlaneSpec]
) -> dict[str, Any]:
    service_name = _compose_plane_service_name(plane)
    image_key = f"plane-{plane.name}"
    definition: dict[str, Any] = {
        "profiles": list(plane.compose_profiles),
        "hostname": service_name,
        "build": {
            "context": plane.build_context,
            "dockerfile": plane.dockerfile,
        },
        "image": f"{plane.image_repository}:{release.image_tag_for(image_key)}",
        "pull_policy": COMPOSE_BUILD_PULL_POLICY,
        "environment": _plane_env_for_compose(plane, planes),
        "expose": [str(plane.container_port)],
    }
    # hostPort 가 지정된 plane(= edge-plane) 만 외부 포트 노출. 그 외는 hostname 통신 전용.
    if plane.host_port is not None:
        definition["ports"] = [f"{plane.host_port}:{plane.container_port}"]
    depends_on: dict[str, dict[str, str]] = {}
    for dependency in plane.infra_dependencies:
        condition = "service_started" if dependency == "ferretdb" else "service_healthy"
        depends_on[dependency] = {"condition": condition}
    if depends_on:
        definition["depends_on"] = depends_on
    # 모든 plane 은 컨테이너 내부에서 localhost:container_port 로 /health 체크.
    # (외부 host port 유무와 무관 — docker healthcheck 는 컨테이너 네트워크 내부에서 실행됨.)
    definition["healthcheck"] = {
        "test": [
            "CMD-SHELL",
            f"python -c 'import urllib.request,sys; "
            f'sys.exit(0 if urllib.request.urlopen("http://localhost:{plane.container_port}{plane.health_path}",timeout=2).status==200 else 1)\'',
        ],
        "interval": "10s",
        "timeout": "3s",
        "retries": 5,
        "start_period": "20s",
    }
    return definition


_EDGE_ROUTER_HOST_PORT = 8080
_EDGE_ROUTER_CONTAINER_PORT = 80
_WEB_CONTAINER_PORT = 3000


def _compose_web_definition(
    web: ServiceSpec, release: ReleaseManifest, planes: dict[str, PlaneSpec]
) -> dict[str, Any]:
    """web(Next.js) 컨테이너 정의. 외부 노출 없음 — edge-router 만 진입."""
    edge_plane = planes["edge"]
    return {
        "profiles": list(web.compose_profiles),
        "hostname": "web",
        "build": {"context": web.build_context, "dockerfile": "Dockerfile"},
        "image": f"{web.image_repository}:{release.image_tag_for(web.name)}",
        "pull_policy": COMPOSE_BUILD_PULL_POLICY,
        "environment": {
            "NODE_ENV": "production",
            "HOSTNAME": "0.0.0.0",  # noqa: S104 — 컨테이너 내부 바인딩, 외부 진입은 edge-router 가 차단
            "PORT": str(_WEB_CONTAINER_PORT),
            # SSR 이 컨테이너 내부에서 호출하는 백엔드 baseURL — edge-plane 직통.
            "NEXT_PUBLIC_API_BASE_URL": (f"http://edge-plane:{edge_plane.container_port}"),
            "NEXT_PUBLIC_DEMO_USERNAME": "${ONEERP_DEV_ADMIN_USERNAME:-demo}",
            "NEXT_PUBLIC_DEMO_PASSWORD": "${ONEERP_DEV_ADMIN_PASSWORD:-demo1234}",
        },
        "expose": [str(_WEB_CONTAINER_PORT)],
        "depends_on": {"edge-plane": {"condition": "service_healthy"}},
        "healthcheck": {
            "test": [
                "CMD-SHELL",
                f'node -e \'require("http").get("http://localhost:{_WEB_CONTAINER_PORT}/",'
                f'r=>process.exit(r.statusCode<500?0:1)).on("error",()=>process.exit(1))\'',
            ],
            "interval": "10s",
            "timeout": "3s",
            "retries": 5,
            "start_period": "30s",
        },
    }


def _compose_edge_router_definition(
    *,
    web_present: bool,
) -> dict[str, Any]:
    """edge-router(Caddy) 컨테이너 정의 — 단일 외부 진입점."""
    depends_on: dict[str, dict[str, str]] = {
        "edge-plane": {"condition": "service_healthy"},
    }
    if web_present:
        depends_on["web"] = {"condition": "service_healthy"}
    return {
        "profiles": ["minimal", "starter", "business", "advanced", "platform", "full"],
        "image": "caddy:2-alpine",
        "hostname": "edge-router",
        "ports": [f"{_EDGE_ROUTER_HOST_PORT}:{_EDGE_ROUTER_CONTAINER_PORT}"],
        "volumes": [
            "./deploy/edge-router/Caddyfile:/etc/caddy/Caddyfile:ro",
            "edge_router_data:/data",
        ],
        "depends_on": depends_on,
        "healthcheck": {
            "test": [
                "CMD-SHELL",
                f"wget --spider -q http://localhost:{_EDGE_ROUTER_CONTAINER_PORT}/ || exit 1",
            ],
            "interval": "10s",
            "timeout": "3s",
            "retries": 5,
            "start_period": "10s",
        },
    }


def render_caddyfile(planes: dict[str, PlaneSpec]) -> str:
    """edge-router(Caddy) 라우팅 규칙. /api/* → edge-plane, /* → web."""
    edge_plane = planes["edge"]
    return dedent(
        f"""\
        # GENERATED FILE. DO NOT EDIT.
        # source: deploy/catalog/planes.yaml, deploy/catalog/services.yaml
        #
        # ADR-0014 단일 외부 진입점 (edge-router):
        #   /api/*  → edge-plane:{edge_plane.container_port} (FastAPI gateway → 도메인 mounts)
        #   /*       → web:{_WEB_CONTAINER_PORT}            (Next.js SSR/static/HMR)
        :{_EDGE_ROUTER_CONTAINER_PORT} {{
        \tlog
        \tencode zstd gzip

        \thandle /api/* {{
        \t\treverse_proxy edge-plane:{edge_plane.container_port}
        \t}}

        \thandle {{
        \t\treverse_proxy web:{_WEB_CONTAINER_PORT}
        \t}}
        }}
        """,
    )


def render_compose_yaml(
    planes: dict[str, PlaneSpec],
    services: dict[str, ServiceSpec],
    release: ReleaseManifest,
) -> str:
    """docker-compose.yml 내용을 렌더링한다 (ADR-0014 6 Plane + web + edge-router)."""
    compose_doc: dict[str, Any] = {
        "name": "oneerp",
        "services": {
            "postgres": {
                "image": "ghcr.io/ferretdb/postgres-documentdb:17-0.107.0-ferretdb-2.7.0",
                "hostname": "postgres",
                "environment": {
                    "POSTGRES_USER": "ferret",
                    "POSTGRES_PASSWORD": "ferret",
                    "POSTGRES_DB": "postgres",
                    "PGDATA": "/var/lib/postgresql/data/pgdata",
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "expose": ["5432"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U ferret -d postgres"],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 5,
                },
            },
            "ferretdb": {
                "image": "ghcr.io/ferretdb/ferretdb:2.7.0",
                "hostname": "ferretdb",
                "environment": {
                    "FERRETDB_POSTGRESQL_URL": "postgres://ferret:ferret@postgres:5432/postgres?sslmode=disable",
                    "FERRETDB_LISTEN_ADDR": "0.0.0.0:27017",
                    "FERRETDB_AUTH": "false",
                    "FERRETDB_LOG_LEVEL": "INFO",
                },
                "expose": ["27017"],
                "depends_on": {"postgres": {"condition": "service_healthy"}},
            },
            "valkey": {
                "image": "valkey/valkey:8",
                "hostname": "valkey",
                "expose": ["6379"],
                "healthcheck": {
                    "test": ["CMD", "valkey-cli", "ping"],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 5,
                },
            },
            "nats": {
                "image": "nats:2.11-alpine",
                "hostname": "nats",
                "command": ["--jetstream", "--store_dir", "/data", "-m", "8222"],
                "expose": ["4222", "8222"],
                "volumes": ["nats_data:/data"],
                "healthcheck": {
                    "test": ["CMD", "wget", "--spider", "-q", "http://localhost:8222/healthz"],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 5,
                },
            },
        },
        "volumes": {"postgres_data": None, "nats_data": None},
    }

    for plane in planes.values():
        compose_doc["services"][_compose_plane_service_name(plane)] = _compose_plane_definition(
            plane, release, planes
        )

    # web(Next.js) — node runtime 서비스. 외부 노출은 edge-router 가 담당.
    web_present = "web" in services
    if web_present:
        compose_doc["services"]["web"] = _compose_web_definition(services["web"], release, planes)

    # 단일 외부 진입점 edge-router(Caddy). /api/* → edge-plane, /* → web.
    compose_doc["services"]["edge-router"] = _compose_edge_router_definition(
        web_present=web_present,
    )
    compose_doc["volumes"]["edge_router_data"] = None

    header = dedent(
        f"""\
        # GENERATED FILE. DO NOT EDIT.
        # source: deploy/catalog/planes.yaml, deploy/catalog/services.yaml, deploy/catalog/releases/current.yaml
        # release: {release.version}
        #
        # ADR-0014 통합 진입 구조:
        #   - plane 간 통신: compose 네트워크 hostname (ex. http://api-plane:8000)
        #   - 외부 진입: edge-router(Caddy) 만 host:8080 노출
        #     · /api/* → edge-plane:8000 (FastAPI gateway → 도메인 mount)
        #     · /*      → web:3000        (Next.js SSR/static)
        #   - 개발자 직접 접근: `docker compose exec <svc> ...` 또는 edge-router 라우팅 사용
        """,
    )
    return header + _dump_yaml(compose_doc)


def render_values_release_yaml(_service: ServiceSpec, image_tag: str) -> str:
    """서비스별 릴리즈 override values를 렌더링한다."""
    header = dedent(
        """\
        # GENERATED FILE. DO NOT EDIT.
        # source: deploy/catalog/releases/current.yaml
        """,
    )
    return header + _dump_yaml({"image": {"tag": image_tag}})


def render_chart_yaml(service: ServiceSpec) -> str:
    """서비스 Helm Chart.yaml 템플릿을 렌더링한다."""
    return dedent(
        f"""\
        apiVersion: v2
        name: oneerp-{service.name}
        description: OneERP {service.name} 서비스
        type: application
        version: 0.1.0
        appVersion: "0.1.0"
        dependencies:
          - name: oneerp-common
            version: "0.1.0"
            repository: "file://../oneerp-common"
        """,
    )


def render_values_yaml(service: ServiceSpec) -> str:
    """서비스 공통 values.yaml 템플릿을 렌더링한다."""
    document: dict[str, Any] = {
        "serviceName": service.name,
        "image": {
            "pullPolicy": "Always",
            "repository": service.image_repository,
        },
        "service": {
            "port": 80,
            "targetPort": service.container_port,
        },
        "autoscaling": {"enabled": False},
        "httproute": {"enabled": True},
    }
    return _dump_yaml(document)


def render_values_prod_yaml(service: ServiceSpec, image_tag: str) -> str:
    """서비스 prod values 템플릿을 렌더링한다."""
    document: dict[str, Any] = {
        "replicaCount": 2 if service.name != "gateway" else 3,
        "image": {"tag": image_tag},
        "debug": "false",
    }
    if service.name == "gateway":
        document["httproute"] = {
            "hostname": os.environ.get("ONEERP_HOSTNAME", "oneerp.example.com"),
            "rules": [{"path": service.route_prefix, "rewritePath": "/"}],
        }
        document["autoscaling"] = {
            "enabled": True,
            "minReplicas": 2,
            "maxReplicas": 8,
            "targetCPUUtilization": 70,
        }
    elif service.name == "web":
        document["httproute"] = {
            "hostname": os.environ.get("ONEERP_HOSTNAME", "oneerp.example.com"),
            "rules": [{"path": "/", "port": 80}],
        }
    else:
        document["httproute"] = {
            "hostname": os.environ.get("ONEERP_HOSTNAME", "oneerp.example.com"),
            "rules": [{"path": service.route_prefix, "rewritePath": "/"}],
        }
    return _dump_yaml(document)


def render_chart_templates() -> dict[str, str]:
    """공통 라이브러리 차트 include 템플릿을 반환한다."""
    return {
        "templates/deployment.yaml": '{{- /* Deployment — 공통 라이브러리 차트 호출 */ -}}\n{{ include "oneerp-common.deployment" . }}\n',
        "templates/service.yaml": '{{- /* Service — 공통 라이브러리 차트 호출 */ -}}\n{{ include "oneerp-common.service" . }}\n',
        "templates/httproute.yaml": '{{- /* HTTPRoute — 공통 라이브러리 차트 호출 */ -}}\n{{ include "oneerp-common.httproute" . }}\n',
        "templates/hpa.yaml": '{{- /* HPA — 공통 라이브러리 차트 호출 */ -}}\n{{ include "oneerp-common.hpa" . }}\n',
        "templates/pdb.yaml": '{{ include "oneerp-common.pdb" . }}\n',
    }


def _write_if_changed(path: Path, content: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def sync_generated_files(
    root: Path,
    services: dict[str, ServiceSpec],
    planes: dict[str, PlaneSpec],
    release: ReleaseManifest,
) -> list[Path]:
    """생성 산출물을 파일 시스템에 반영한다."""
    changed: list[Path] = []
    targets = {
        root / "docker-compose.yml": render_compose_yaml(planes, services, release),
        root / "deploy" / "edge-router" / "Caddyfile": render_caddyfile(planes),
    }
    for service in services.values():
        if service.k8s_enabled:
            targets[root / "deploy" / "charts" / service.name / "values-release.yaml"] = (
                render_values_release_yaml(service, release.image_tag_for(service.name))
            )

    for path, content in targets.items():
        if _write_if_changed(path, content):
            changed.append(path)
    return changed


def scaffold_service_assets(root: Path, services: dict[str, ServiceSpec]) -> list[Path]:
    """카탈로그 서비스의 누락된 Helm chart 자산을 생성한다.

    ADR-0014 이후 도메인별 Dockerfile 은 생성하지 않는다. 컨테이너는 6 Plane Dockerfile
    (planes/*/Dockerfile) 로만 구성된다.
    """
    changed: list[Path] = []
    for service in services.values():
        if service.k8s_enabled:
            chart_root = root / "deploy" / "charts" / service.name
            chart_targets = {
                chart_root / "Chart.yaml": render_chart_yaml(service),
                chart_root / "values.yaml": render_values_yaml(service),
                chart_root / "values-prod.yaml": render_values_prod_yaml(service, "latest"),
            }
            for relative_path, content in render_chart_templates().items():
                chart_targets[chart_root / relative_path] = content
            for path, content in chart_targets.items():
                if not path.exists() and _write_if_changed(path, content):
                    changed.append(path)
    return changed


def validate_generated_files(
    root: Path,
    services: dict[str, ServiceSpec],
    planes: dict[str, PlaneSpec],
    release: ReleaseManifest,
) -> list[str]:
    """현재 저장소 산출물이 카탈로그와 일치하는지 확인한다."""
    expected = {
        root / "docker-compose.yml": render_compose_yaml(planes, services, release),
        root / "deploy" / "edge-router" / "Caddyfile": render_caddyfile(planes),
    }
    for service in services.values():
        if service.k8s_enabled:
            expected[root / "deploy" / "charts" / service.name / "values-release.yaml"] = (
                render_values_release_yaml(service, release.image_tag_for(service.name))
            )

    errors: list[str] = []
    for path, content in expected.items():
        if not path.exists():
            errors.append(f"누락: {path.relative_to(root)}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != content:
            errors.append(f"드리프트: {path.relative_to(root)}")
    return errors
