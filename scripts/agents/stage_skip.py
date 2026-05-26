"""변경 파일 목록 + plan 메타 → Stage skip 집합 평가.

룰:
- BE 변경 없음 (`services/`, `packages/core/` 미포함) → "be" skip
- typebridge: BE 변경 없음 OR 공개 인터페이스 미변경 → "typebridge" skip
- FE 변경 없음 (`web/` 미포함) → "fe", "visual" skip
- plan_meta.pipeliner_skip_stages 의 항목은 항상 skip 추가
"""

from __future__ import annotations

from typing import Final

BE_PREFIXES: Final[tuple[str, ...]] = ("services/", "packages/core/")
FE_PREFIX: Final[str] = "web/"


def _has_prefix(files: list[str], prefixes: tuple[str, ...] | str) -> bool:
    if isinstance(prefixes, str):
        return any(f.startswith(prefixes) for f in files)
    return any(f.startswith(p) for f in files for p in prefixes)


def evaluate_skip(
    *,
    changed_files: list[str],
    plan_meta: dict | None,
    public_iface_changed: bool,
) -> set[str]:
    """Stage skip 집합 반환.

    반환 원소는 stage 이름 문자열 (`"be"`, `"typebridge"`, `"fe"`, `"visual"`)이며
    T7 oe-feature-pipeliner의 각 Stage entry 조건과 1:1 대응한다.
    """
    skip: set[str] = set()
    has_be = _has_prefix(changed_files, BE_PREFIXES)
    has_fe = _has_prefix(changed_files, FE_PREFIX)
    if not has_be:
        skip.add("be")
    typebridge_needed = has_be and public_iface_changed
    if not typebridge_needed:
        skip.add("typebridge")
    if not has_fe:
        skip.add("fe")
        skip.add("visual")
    # plan 메타 명시 skip override
    if plan_meta and isinstance(plan_meta.get("pipeliner_skip_stages"), list):
        for s in plan_meta["pipeliner_skip_stages"]:
            skip.add(str(s))
    return skip
