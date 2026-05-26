"""Worker Plane 진입점 — ADR-0014 M2.

각 도메인의 `oneerp_{svc}_app.events.event_registry` 를 수집하여 단일
EventHandlerRegistry 로 병합한 뒤, create_service_app 의 이벤트 lifespan 에
위임하여 NATS JetStream 구독을 일괄 등록한다.

실행:
    uv run --package oneerp-plane-worker --directory planes/worker_plane \\
        uvicorn plane_worker.main:app --port 8102
"""

from __future__ import annotations

import logging
from pathlib import Path

from oneerp_core.app_factory import create_service_app
from oneerp_core.events import EventHandlerRegistry
from plane_shared.assembler import (  # type: ignore[unresolved-import]
    DomainMount,
    load_domain_module,
)

logger = logging.getLogger("plane.worker")

_REPO_ROOT = Path(__file__).resolve().parents[3]

# 실제 수신 핸들러가 존재하는 도메인만 포함.
# crm/manufacturing/hr/assets 는 발행자 역할만 완성되어 있으며, 수신 핸들러는 비즈니스 요구
# 확정 시 별도 spec 으로 추가한다 (spec 2026-04-13-worker-subscription-cleanup §7).
_EVENT_DOMAINS: list[tuple[str, str, str]] = [
    ("selling", "sales", "selling"),
    ("stock", "scm", "stock"),
    ("buying", "scm", "buying"),
    ("accounting", "finance", "accounting"),
    ("payroll", "finance", "payroll"),
    ("expenses", "finance", "expenses"),
    ("plm", "assets", "plm"),
]


def _event_mount(name: str, *parts: str) -> DomainMount:
    return DomainMount(name=name, service_root=_REPO_ROOT.joinpath("services", *parts))


def _load_domain_registry(mount: DomainMount) -> EventHandlerRegistry | None:
    """도메인의 events.event_registry 를 로드. 없으면 None."""
    try:
        mod = load_domain_module(mount, module_name="events")
    except FileNotFoundError:
        logger.warning("도메인 %s: 진입 패키지 없음, 건너뜀", mount.name)
        return None
    except ModuleNotFoundError as e:
        logger.warning("도메인 %s: events 모듈 없음 (%s)", mount.name, e)
        return None

    reg = getattr(mod, "event_registry", None)
    if reg is None or not isinstance(reg, EventHandlerRegistry):
        logger.warning("도메인 %s: event_registry 심볼 없음", mount.name)
        return None
    return reg


def _collect_master_registry() -> EventHandlerRegistry:
    """전 도메인 레지스트리를 master 하나로 병합."""
    master = EventHandlerRegistry()
    total = 0
    for name, *parts in _EVENT_DOMAINS:
        mount = _event_mount(name, *parts)
        reg = _load_domain_registry(mount)
        if reg is None:
            continue
        for sub in reg.subscriptions:
            master.register_handler(
                sub.event_type,
                sub.handler,
                description=f"[{name}] {sub.description}",
            )
            total += 1
        logger.info("도메인 %s: %d 구독 등록", mount.name, len(reg.subscriptions))
    logger.info("Worker Plane master 레지스트리: 총 %d 구독", total)
    return master


_MASTER_REGISTRY = _collect_master_registry()

app = create_service_app(
    service_name="plane-worker",
    event_registry=_MASTER_REGISTRY,
)
