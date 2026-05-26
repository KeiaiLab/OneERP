"""Edit 직후 grep ground-truth 검증 헬퍼.

Edit 도구가 성공을 반환했더라도 *파일에 변경이 실제 적용됐다는 보증은 아님*.
(CLAUDE.md §8 cycle 1 학습: "Edit success ≠ 적용 보증")
이 모듈은 (파일, 인용 문자열) 쌍의 grep 결과를 강제 검증한다.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Final

_EXPECTED_PREVIEW_LEN: Final[int] = 30


class GroundTruthMismatch(RuntimeError):
    """ground-truth 검증 실패 — Edit이 파일에 적용되지 않았거나 파일 부재."""


def verify_edit(file_path: Path, expected: str) -> bool:
    """파일에 expected 문자열이 존재하는지 검증.

    파일이 없으면 False (예외 없이 — caller가 raise_on_miss로 결정).
    """
    if not file_path.is_file():
        return False
    text = file_path.read_text(encoding="utf-8")
    return expected in text


def verify_edits(
    edits: Iterable[tuple[Path, str]],
    *,
    raise_on_miss: bool = False,
) -> list[tuple[Path, str]]:
    """다수 (파일, 인용) 쌍 검증. 미스 목록 반환.

    raise_on_miss=True 시 미스 발견 즉시 GroundTruthMismatch.
    """
    misses: list[tuple[Path, str]] = []
    for path, expected in edits:
        if not verify_edit(path, expected):
            misses.append((path, expected))
    if misses and raise_on_miss:
        details = ", ".join(f"{p}: {e[:_EXPECTED_PREVIEW_LEN]!r}" for p, e in misses)
        raise GroundTruthMismatch(f"존재하지 않는 파일 또는 매칭 실패: {details}")
    return misses
