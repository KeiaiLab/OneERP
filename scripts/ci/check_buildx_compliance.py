#!/usr/bin/env python3
"""buildx 규약 컴플라이언스 체크 (CLAUDE.md + ADR-0010 §2.1).

배경: CLAUDE.md 전역 규칙 — "배포 컨테이너 이미지는 `docker buildx` +
`masblue-builder` 로 빌드한다. `--platform` 생략 시 자동 linux/amd64.
멀티아키텍처 빌드 금지." 하지만 6개 plane Dockerfile 은 단일 stage 로만
정의되어 있어 순정 `docker build` 호출로도 빌드될 수 있다. 본 체크는
`scripts/build/build-planes.sh` 가 모든 plane 을 `docker buildx build
--platform linux/amd64` 패턴으로 호출하는지 정적 검사한다.

사용:
    python3 scripts/ci/check_buildx_compliance.py
    # exit 0: 모든 plane buildx+amd64 단일 아키텍처로 커버됨
    # exit 1: 위반

TDD 테스트: tests/unit/test_buildx_compliance.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

BUILD_SCRIPT = "scripts/build/build-planes.sh"
PLANES_DIR = "planes"
BUILDX_LINE_RE = re.compile(r"docker\s+buildx\s+build[^\n]*", re.IGNORECASE)
PLATFORM_RE = re.compile(r"--platform[=\s]+(\S+)")
DOCKERFILE_REF_RE = re.compile(r"-f\s+(\S+Dockerfile)")


@dataclass
class CheckResult:
    ok: bool
    reason: str = ""


def _discover_planes(repo: Path) -> list[str]:
    """planes/*/Dockerfile 보유 plane 이름 목록 반환."""
    root = repo / PLANES_DIR
    if not root.is_dir():
        return []
    return [d.name for d in sorted(root.iterdir()) if d.is_dir() and (d / "Dockerfile").is_file()]


def check(repo: Path) -> CheckResult:
    """buildx 규약 컴플라이언스 정적 검사.

    반환: ok=True 이면 규약 준수. ok=False 이면 reason 에 위반 사유.
    """
    planes = _discover_planes(repo)
    if not planes:
        return CheckResult(ok=True, reason="no planes/ Dockerfile found — skip")

    script = repo / BUILD_SCRIPT
    if not script.is_file():
        return CheckResult(
            ok=False,
            reason=f"{BUILD_SCRIPT} missing — buildx 규약 SoT 필요 (planes: {', '.join(planes)})",
        )

    text = script.read_text(encoding="utf-8", errors="ignore")
    buildx_lines = BUILDX_LINE_RE.findall(text)
    if not buildx_lines:
        return CheckResult(
            ok=False,
            reason=f"{BUILD_SCRIPT} 에 `docker buildx build` 호출 없음 "
            "(ADR-0010 §2.1, CLAUDE.md 전역 규칙)",
        )

    # 멀티 아키텍처 금지 검사
    for line in buildx_lines:
        m = PLATFORM_RE.search(line)
        platform = m.group(1) if m else "linux/amd64"
        # 쉼표 포함 = 멀티 아키텍처
        if "," in platform:
            return CheckResult(
                ok=False,
                reason=f"multi-arch 빌드 금지 (CLAUDE.md). 발견: --platform {platform}",
            )
        if platform != "linux/amd64":
            return CheckResult(
                ok=False,
                reason=f"linux/amd64 외 플랫폼 금지. 발견: --platform {platform}",
            )

    # 모든 plane 이 스크립트에서 참조되는지 확인.
    # 리터럴 `-f planes/<plane>/Dockerfile` 또는 스크립트 본문에 plane 이름이 있는지.
    referenced_dockerfiles = {m.strip() for m in DOCKERFILE_REF_RE.findall(text)}
    missing: list[str] = []
    for plane in planes:
        expected_suffix = f"{PLANES_DIR}/{plane}/Dockerfile"
        literal = any(ref.endswith(expected_suffix) for ref in referenced_dockerfiles)
        # 동적 루프 허용: plane 이름이 스크립트에 나타나면 커버된 것으로 간주.
        # 오탐 방지를 위해 단어 경계 체크.
        dynamic = re.search(rf"\b{re.escape(plane)}\b", text) is not None
        if not (literal or dynamic):
            missing.append(plane)
    if missing:
        return CheckResult(
            ok=False,
            reason=f"{BUILD_SCRIPT} 미커버 plane: {', '.join(missing)}",
        )

    return CheckResult(
        ok=True, reason=f"ok — {len(planes)} planes buildx+linux/amd64 단일 아키텍처"
    )


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    result = check(repo)
    if result.ok:
        print(f"[buildx-compliance] PASS — {result.reason}")
        return 0
    print(f"[buildx-compliance] FAIL — {result.reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
