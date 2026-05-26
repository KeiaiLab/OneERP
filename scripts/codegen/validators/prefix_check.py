"""naming_prefix 중복 검사."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from scripts.codegen.catalog import CatalogEntry


def check_duplicate_prefixes(
    entries: Sequence[CatalogEntry],
) -> dict[str, list[str]]:
    """중복된 naming_prefix를 찾아 반환한다.

    반환: {중복_prefix: [엔티티명1, 엔티티명2, ...]}
    """
    prefix_map: dict[str, list[str]] = {}
    for entry in entries:
        if not entry.naming_prefix:
            continue
        prefix_map.setdefault(entry.naming_prefix, []).append(
            entry.doctype_or_entity,
        )

    return {
        prefix: entities for prefix, entities in sorted(prefix_map.items()) if len(entities) > 1
    }


def print_prefix_report(
    duplicates: dict[str, list[str]],
) -> None:
    """중복 prefix 보고서를 콘솔에 출력한다."""
    if not duplicates:
        print("[OK] naming_prefix 중복 없음")
        return

    print(f"[경고] naming_prefix 중복 발견 ({len(duplicates)}건):")
    for prefix, entities in duplicates.items():
        print(f"  {prefix}: {', '.join(entities)}")


def check_empty_prefixes(
    entries: Sequence[CatalogEntry],
) -> list[str]:
    """naming_prefix가 비어있는 엔티티를 찾아 반환한다."""
    return [entry.doctype_or_entity for entry in entries if not entry.naming_prefix.strip()]
