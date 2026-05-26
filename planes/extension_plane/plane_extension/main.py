"""Extension Plane 진입점 (ADR-0014).

플랫폼 확장 지점 + 저빈도 도메인 오프로드:
- 외부 어댑터: iot, integration-hub
- 마케팅: marketing, marketing-automation, gtm
- 협업/지식: board, projects, wiki, knowledge, documents, survey
"""

from __future__ import annotations

from pathlib import Path

from plane_shared import DomainMount, build_plane_app

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _mount(name: str, *parts: str) -> DomainMount:
    return DomainMount(name=name, service_root=_REPO_ROOT.joinpath("services", *parts))


_MOUNTS: list[DomainMount] = [
    # 외부 어댑터
    _mount("iot", "platform", "iot"),
    _mount("integration-hub", "platform", "integration-hub"),
    # 마케팅
    _mount("marketing", "marketing", "marketing"),
    _mount("marketing-automation", "marketing", "marketing-automation"),
    _mount("gtm", "marketing", "gtm"),
    # 협업/지식
    _mount("board", "collab", "board"),
    _mount("projects", "collab", "projects"),
    _mount("wiki", "collab", "wiki"),
    _mount("knowledge", "collab", "knowledge"),
    _mount("documents", "collab", "documents"),
    _mount("survey", "collab", "survey"),
]

app = build_plane_app(plane_name="extension", mounts=_MOUNTS)
