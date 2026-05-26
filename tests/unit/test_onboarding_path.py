"""QUICKSTART 링크 체인 4-hop 정확성 검증.

목표: README → QUICKSTART.md → (다음 단계 5개) 링크가 전부 실재 파일을 가리키고,
신규 기여자가 문서 미로에 빠지지 않도록 한다.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
QUICKSTART = ROOT / "docs" / "onboarding" / "QUICKSTART.md"

# QUICKSTART 에서 "다음 단계" 섹션이 가리켜야 하는 5개 핵심 문서
NEXT_STEP_TARGETS = [
    ROOT / "docs" / "STATUS.md",
    ROOT / "docs" / "product" / "scope" / "MODULE-SERVICE-MAP.md",
    ROOT / "docs" / "tutorials" / "01-order-to-cash.md",
    ROOT / "docs" / "onboarding" / "01-architecture-overview.md",
    ROOT / "docs" / "onboarding" / "02-coding-guide.md",
]


def test_quickstart_파일_존재() -> None:
    assert QUICKSTART.exists(), (
        f"{QUICKSTART.relative_to(ROOT)} 가 없음 — M0 PR-0.7 에서 신규 생성되어야 함"
    )


def test_readme_에서_quickstart_단일링크() -> None:
    """README 가 QUICKSTART.md 로 가는 링크를 1회 이상 포함."""
    text = README.read_text(encoding="utf-8")
    assert "docs/onboarding/QUICKSTART.md" in text, (
        "README.md 상단에 docs/onboarding/QUICKSTART.md 링크가 있어야 합니다."
    )


def test_quickstart_다음단계_5개_링크가_실재파일() -> None:
    """QUICKSTART '다음 단계' 5 링크 모두 실재 파일을 가리켜야 함."""
    for target in NEXT_STEP_TARGETS:
        assert target.exists(), (
            f"QUICKSTART 다음단계 링크가 가리키는 파일이 없음: {target.relative_to(ROOT)}"
        )


def test_quickstart_가_next_step_타겟을_모두_참조() -> None:
    """QUICKSTART 본문에 5개 다음단계 파일 경로가 모두 등장."""
    body = QUICKSTART.read_text(encoding="utf-8")
    missing: list[str] = []
    for target in NEXT_STEP_TARGETS:
        # QUICKSTART 기준 상대경로 (docs/onboarding/QUICKSTART.md 에서 상대)
        try:
            rel = target.relative_to(QUICKSTART.parent).as_posix()
        except ValueError:
            # 상위 디렉토리로 거슬러 올라가는 경우 ../ 형식
            rel = "../" + target.relative_to(QUICKSTART.parent.parent).as_posix()
        if rel not in body and target.name not in body:
            missing.append(rel)
    assert not missing, f"QUICKSTART '다음 단계' 섹션에 누락된 링크: {missing}"


def test_quickstart_내_상대경로_링크_깨짐없음() -> None:
    """QUICKSTART 본문의 모든 Markdown 링크 타겟이 실재 파일이어야 함 (외부 URL 제외)."""
    body = QUICKSTART.read_text(encoding="utf-8")
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    broken: list[str] = []
    for m in link_pattern.finditer(body):
        href = m.group(1)
        # 외부 링크·앵커-only 는 스킵
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        # 앵커 제거 (#section)
        path_part = href.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (QUICKSTART.parent / path_part).resolve()
        if not resolved.exists():
            broken.append(href)
    assert not broken, f"QUICKSTART 본문에 깨진 링크가 있습니다: {broken}"
