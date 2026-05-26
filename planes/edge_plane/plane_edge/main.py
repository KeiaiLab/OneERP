"""Edge Plane 진입점."""

from __future__ import annotations

from pathlib import Path

from plane_shared import DomainMount, build_plane_app  # type: ignore[unresolved-import]

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _mount(name: str, *parts: str) -> DomainMount:
    return DomainMount(name=name, service_root=_REPO_ROOT.joinpath("services", *parts))


_GATEWAY_MOUNTS: list[DomainMount] = [
    # edge plane 의 실행형 진실은 gateway 서브앱을 /api/gateway 아래에 조립하는 것이다.
    # 외부 라우팅 계약은 유지하고, plane 은 조립 책임만 가진다.
    _mount("api/gateway", "platform", "gateway"),
]

app = build_plane_app(plane_name="edge", mounts=_GATEWAY_MOUNTS)
