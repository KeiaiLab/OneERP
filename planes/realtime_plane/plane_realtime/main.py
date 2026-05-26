"""Realtime Plane 진입점."""

from __future__ import annotations

from pathlib import Path

from plane_shared import DomainMount, build_plane_app

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _mount(name: str, *parts: str) -> DomainMount:
    return DomainMount(name=name, service_root=_REPO_ROOT.joinpath("services", *parts))


_MOUNTS: list[DomainMount] = [
    _mount("portal", "portal", "portal_core"),
    _mount("comms", "portal", "portal_comms"),
    _mount("calendar", "collab", "calendar"),
]

app = build_plane_app(plane_name="realtime", mounts=_MOUNTS)
