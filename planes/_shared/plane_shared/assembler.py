"""Plane assembler — 도메인 서비스 FastAPI 앱을 Runtime Plane에 마운트한다.

ADR-0014(Runtime-Plane 분해) 구현 1단계. 각 Plane은 이 assembler를 사용하여
`services/{domain}/app/main:app` 인스턴스를 URL 경로 prefix로 마운트한다.

M1 제약 — 단일 도메인 마운트만 안전하다:
    현재 모든 서비스가 `packages = ["app"]` 로 최상위 패키지명을 공유하고
    (`docs/engineering/msa/RUNBOOK-cluster-merge.md` 제약 A),
    도메인 코드 안에서 `from app.entities import ...` 같은 **절대 import**가
    다수 존재한다 (selling 39건, stock 25건 — 2026-04-12 기준).

    따라서 `sys.modules["app"]` 슬롯이 단일 점유되어 한 프로세스에
    두 도메인을 동시 로드할 수 없다. M1.5에서 도메인별 패키지명 리네임
    (`packages = ["oneerp_{domain}_app"]`)이 선결되면 다중 마운트가
    가능해진다.

    M1에서는 DomainMount 리스트가 1개 이상이면 명시적 ValueError를 던져
    silent 충돌을 방지한다.
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from oneerp_core.app_factory import create_service_app
from oneerp_core.testing import _detect_service_package

if TYPE_CHECKING:
    from pathlib import Path
    from types import ModuleType

    from fastapi import FastAPI  # type: ignore[unresolved-import]


@dataclass(frozen=True)
class DomainMount:
    """도메인 한 개의 plane 마운트 설정.

    Attributes:
        name: URL prefix 및 로깅 식별자 (예: "selling").
        service_root: 도메인 서비스 루트 (예: `services/sales/selling`).
    """

    name: str
    service_root: Path


def load_domain_app(mount: DomainMount) -> FastAPI:
    """도메인 서비스의 FastAPI 앱을 로드한다.

    `services/{domain}/app/main.py`의 `app` 심볼을 반환한다.
    `sys.path` 최상단에 도메인 루트를 배치하여 `from app.*` 절대 import를 해석한다.

    Args:
        mount: 로드할 도메인 마운트 설정.

    Returns:
        도메인의 FastAPI app 인스턴스.

    Raises:
        FileNotFoundError: service_root 가 존재하지 않을 때.
        ImportError: `app.main` 을 해석할 수 없을 때.
    """
    module = load_domain_module(mount, module_name="main")
    return module.app


def _prune_service_paths(service_root: Path) -> None:
    """레거시 `app` 절대 import 충돌을 피하도록 서비스 import root 를 고립한다."""
    root_str = str(service_root)
    for path_entry in list(sys.path):
        if (
            "/services/" in path_entry
            and "/.venv/" not in path_entry
            and root_str not in path_entry
        ):
            sys.path.remove(path_entry)

    if root_str in sys.path:
        sys.path.remove(root_str)
    sys.path.insert(0, root_str)


def _clear_service_package_cache(*, package_name: str, service_root: Path) -> None:
    """현재 서비스 바깥에서 로드된 동명 패키지 캐시를 제거한다."""
    root_str = str(service_root)
    for key in [
        k for k in tuple(sys.modules) if k == package_name or k.startswith(f"{package_name}.")
    ]:
        mod_file = getattr(sys.modules[key], "__file__", "") or ""
        if root_str not in mod_file:
            del sys.modules[key]


def load_domain_module(mount: DomainMount, *, module_name: str) -> ModuleType:
    """도메인 서비스의 Python 모듈을 plane 조립 컨텍스트로 로드한다."""
    root = mount.service_root.resolve()
    package_name = _detect_service_package(root)  # "app" 또는 "oneerp_{service}_app"

    _clear_service_package_cache(package_name=package_name, service_root=root)
    _prune_service_paths(root)

    return importlib.import_module(f"{package_name}.{module_name}")


def build_plane_app(
    *,
    plane_name: str,
    mounts: list[DomainMount],
) -> FastAPI:
    """Plane 진입점 FastAPI 앱을 구성한다.

    각 도메인 서비스 앱을 `/{mount.name}` 경로에 ASGI 서브앱으로 마운트한다.
    서브앱의 lifespan/middleware/라우터는 그대로 유지된다.

    Args:
        plane_name: Plane 식별자 (예: "api", "worker").
        mounts: 마운트할 도메인 리스트. M1에서는 길이 1만 허용.

    Returns:
        마운트 완료된 plane 레벨 FastAPI 앱.

    Raises:
        ValueError: 다중 마운트 요청 (M1 제약 — M1.5 리네임 선결 필요).
    """
    if not mounts:
        raise ValueError(f"plane '{plane_name}': 최소 1개 도메인 마운트 필요")
    # M1.5 이후 다중 도메인 마운트 허용 — 단, 모든 도메인이 `oneerp_*_app` 로
    # 리네임됐거나(권장), 레거시 `app` 패키지를 단일 도메인만 사용하는 경우.
    legacy_app_count = sum(1 for m in mounts if (m.service_root / "app" / "main.py").is_file())
    if legacy_app_count > 1:
        raise ValueError(
            f"plane '{plane_name}': 레거시 `app` 패키지 단일 점유 충돌. "
            f"리네임되지 않은 도메인이 2개 이상: "
            f"{[m.name for m in mounts if (m.service_root / 'app' / 'main.py').is_file()]}. "
            "scripts/codemod/rename_service_package.py 로 리네임 후 재시도."
        )

    plane_app = create_service_app(service_name=f"plane-{plane_name}")
    for mount in mounts:
        sub_app = load_domain_app(mount)
        plane_app.mount(f"/{mount.name}", sub_app, name=mount.name)
    return plane_app
