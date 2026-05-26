"""배포 카탈로그 로더.

단일 SoT인 deploy/catalog 하위 YAML을 읽어 compose/K8s 생성기의 입력으로 변환한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class ServiceSpec:
    """단일 서비스 배포 정의."""

    name: str
    runtime: str
    source_dir: str
    image_repository: str
    route_prefix: str
    compose_profiles: tuple[str, ...]
    container_port: int
    build_context: str
    environment: dict[str, str]
    infra_dependencies: tuple[str, ...]
    local_debug_port: int | None
    package: str | None
    compose_enabled: bool
    k8s_enabled: bool


@dataclass(frozen=True, slots=True)
class PlaneSpec:
    """ADR-0014 Runtime Plane 단일 정의.

    48 도메인은 services.yaml(Helm SoT) 에서 유지되고, 컨테이너 경계는
    본 스펙 6개로 수렴한다. plane 간 통신은 compose 네트워크 hostname 기반이며,
    edge-plane 만 외부 host port 를 기본 노출한다.
    """

    name: str
    dockerfile: str
    image_repository: str
    compose_profiles: tuple[str, ...]
    container_port: int
    build_context: str
    environment: dict[str, str]
    infra_dependencies: tuple[str, ...]
    host_port: int | None
    health_path: str


@dataclass(frozen=True, slots=True)
class ReleaseService:
    """릴리즈별 서비스 이미지 정보."""

    name: str
    image_tag: str


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    """플랫폼 릴리즈 manifest."""

    version: str
    default_image_tag: str
    services: dict[str, ReleaseService]

    def image_tag_for(self, service_name: str) -> str:
        """서비스별 이미지 태그를 반환한다. 미등록 이름은 default_image_tag 으로 fallback."""
        if service_name in self.services:
            return self.services[service_name].image_tag
        return self.default_image_tag


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        loaded = yaml.safe_load(file)
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML 루트는 mapping 이어야 한다: {path}")
    return loaded


def _catalog_root(root: Path) -> Path:
    return root / "deploy" / "catalog"


def load_service_catalog(root: Path) -> dict[str, ServiceSpec]:
    """서비스 배포 카탈로그를 로드한다."""
    raw = _read_yaml(_catalog_root(root) / "services.yaml")
    defaults = raw.get("defaults", {})
    services = raw.get("services", {})
    if not isinstance(defaults, dict) or not isinstance(services, dict):
        raise ValueError("services.yaml 구조가 올바르지 않다")

    loaded: dict[str, ServiceSpec] = {}
    for name, service_raw in services.items():
        if not isinstance(service_raw, dict):
            raise ValueError(f"서비스 정의는 mapping 이어야 한다: {name}")
        runtime = str(
            service_raw.get("runtime", defaults.get("python", {}).get("runtime", "python"))
        )
        runtime_defaults = defaults.get(runtime, {})
        if not isinstance(runtime_defaults, dict):
            raise ValueError(f"기본 runtime 정의가 없다: {runtime}")

        merged_env = dict(runtime_defaults.get("environment", {}))
        merged_env.update(service_raw.get("environment", {}))
        infra_dependencies = tuple(
            str(item)
            for item in service_raw.get(
                "infraDependencies",
                runtime_defaults.get("infraDependencies", []),
            )
        )
        profiles = tuple(str(item) for item in service_raw.get("composeProfiles", []))
        local_debug_port = service_raw.get("localDebugPort")
        loaded[name] = ServiceSpec(
            name=name,
            runtime=runtime,
            source_dir=str(service_raw["sourceDir"]),
            image_repository=str(service_raw["imageRepository"]),
            route_prefix=str(service_raw["routePrefix"]),
            compose_profiles=profiles,
            container_port=int(service_raw.get("containerPort", runtime_defaults["containerPort"])),
            build_context=str(
                service_raw.get("buildContext", runtime_defaults.get("buildContext", "."))
            ),
            environment={str(key): str(value) for key, value in merged_env.items()},
            infra_dependencies=infra_dependencies,
            local_debug_port=int(local_debug_port) if local_debug_port is not None else None,
            package=str(service_raw["package"]) if "package" in service_raw else None,
            compose_enabled=bool(service_raw.get("composeEnabled", True)),
            k8s_enabled=bool(service_raw.get("k8sEnabled", False)),
        )
    return loaded


def load_plane_catalog(root: Path) -> dict[str, PlaneSpec]:
    """Runtime Plane 카탈로그를 로드한다."""
    raw = _read_yaml(_catalog_root(root) / "planes.yaml")
    defaults = raw.get("defaults", {})
    planes = raw.get("planes", {})
    if not isinstance(defaults, dict) or not isinstance(planes, dict):
        raise ValueError("planes.yaml 구조가 올바르지 않다")

    loaded: dict[str, PlaneSpec] = {}
    for name, plane_raw in planes.items():
        if not isinstance(plane_raw, dict):
            raise ValueError(f"plane 정의는 mapping 이어야 한다: {name}")

        merged_env = dict(defaults.get("environment", {}))
        merged_env.update(plane_raw.get("environment", {}))
        infra_dependencies = tuple(
            str(item)
            for item in plane_raw.get(
                "infraDependencies",
                defaults.get("infraDependencies", []),
            )
        )
        profiles = tuple(str(item) for item in plane_raw.get("composeProfiles", []))
        host_port = plane_raw.get("hostPort")
        loaded[name] = PlaneSpec(
            name=name,
            dockerfile=str(plane_raw["dockerfile"]),
            image_repository=str(plane_raw["imageRepository"]),
            compose_profiles=profiles,
            container_port=int(plane_raw.get("containerPort", defaults.get("containerPort", 8000))),
            build_context=str(plane_raw.get("buildContext", defaults.get("buildContext", "."))),
            environment={str(key): str(value) for key, value in merged_env.items()},
            infra_dependencies=infra_dependencies,
            host_port=int(host_port) if host_port is not None else None,
            health_path=str(plane_raw.get("healthPath", "/health")),
        )
    return loaded


def load_release_manifest(root: Path) -> ReleaseManifest:
    """현재 릴리즈 manifest를 로드한다."""
    raw = _read_yaml(_catalog_root(root) / "releases" / "current.yaml")
    services = raw.get("services", {})
    if not isinstance(services, dict):
        raise ValueError("release manifest의 services가 mapping이 아니다")

    default_tag = str(raw.get("defaultImageTag", "latest"))
    return ReleaseManifest(
        version=str(raw["version"]),
        default_image_tag=default_tag,
        services={
            name: ReleaseService(
                name=name,
                image_tag=str(config.get("imageTag", default_tag))
                if isinstance(config, dict)
                else default_tag,
            )
            for name, config in services.items()
        },
    )
