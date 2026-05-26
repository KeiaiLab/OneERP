"""T2 tier CI artifact 수집기.

Spec II 회귀(run-*.json 미수집으로 4셀 PARTIAL)를 차단하기 위한 전용 모듈.

GitHub Actions artifact 이름 규칙은 ``t2-<GATE>-<MODULE>-<suffix>`` 이며,
이 모듈은 해당 artifact 를 ``artifacts/T2/<GATE>/<MODULE>/run-<UTC ISO>.json``
경로로 일관되게 재배치한다. CI 워크플로와 게이트 오디터가 동일한 glob
매트릭스를 공유하도록 ``build_expected_globs`` 를 공용 API 로 노출한다.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# why: 엄격 정규식으로 오타·잘못된 이름을 즉시 실패시켜 Spec II 회귀를 차단한다.
_NAME_RE = re.compile(r"^t2-(G\d-\d)-([a-z][a-z0-9-]*)-[a-z0-9-]+$")

_logger = logging.getLogger(__name__)


def normalize_artifact_name(name: str) -> tuple[str, str]:
    """artifact 이름에서 (gate, module) 을 추출한다.

    why: 수집기 입구에서 계약 위반을 ValueError 로 끊어 다운스트림 배치 오류를 방지.
    """
    m = _NAME_RE.match(name)
    if not m:
        raise ValueError(f"bad artifact name: {name!r}")
    return m.group(1), m.group(2)


def place_artifact(src: Path, *, gate: str, module: str, root: Path) -> Path:
    """src 파일을 ``<root>/T2/<gate>/<module>/run-<UTC ISO>.json`` 으로 복사한다.

    why: 경로 규약 고정으로 게이트 오디터의 glob 검증과 1:1 대응시킨다.
    """
    dest_dir = root / "T2" / gate / module
    dest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = dest_dir / f"run-{ts}.json"
    shutil.copy2(src, dest)
    return dest


def build_expected_globs(*, gates: Sequence[str], modules: Sequence[str]) -> list[str]:
    """게이트/모듈 직교 매트릭스의 예상 artifact glob 목록을 생성한다.

    why: 수집기·게이트 오디터가 동일한 기대 집합을 공유해 수집 누락을 드러내도록.
    """
    return [f"artifacts/T2/{g}/{m}/run-*.json" for g in gates for m in modules]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="T2 artifact 를 표준 경로로 배치")
    p.add_argument("--src", type=Path, required=True, help="다운로드된 artifact 파일")
    p.add_argument("--name", required=True, help="artifact 이름 (t2-G*-<module>-*)")
    p.add_argument("--root", type=Path, default=Path("artifacts"))
    return p


def main(argv: Sequence[str] | None = None) -> int:
    """CLI 진입점 — 결과를 stdout 에 JSON 으로 기록한다.

    why: print() 금지 규칙에 따라 json.dump(sys.stdout) 로 구조화 출력만 허용.
    """
    ns = _build_parser().parse_args(argv)
    gate, module = normalize_artifact_name(ns.name)
    dest = place_artifact(ns.src, gate=gate, module=module, root=ns.root)
    json.dump({"placed": str(dest)}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
