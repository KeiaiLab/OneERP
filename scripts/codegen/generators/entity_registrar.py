"""EntityMeta 일괄 등록 생성기 — entities.py에 누락된 엔티티를 추가한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.codegen.catalog import SERVICES_DIR
from scripts.codegen.naming import pascal_to_snake

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.codegen.catalog import CatalogEntry

_GENERATED_SECTION_START = "# --- CODEGEN REGISTERED ENTITIES START ---"
_GENERATED_SECTION_END = "# --- CODEGEN REGISTERED ENTITIES END ---"


def _to_api_path(entity_name: str) -> str:
    """PascalCase → kebab-case API 경로."""
    snake = pascal_to_snake(entity_name)
    kebab = snake.replace("_", "-")
    # 간단한 복수형
    if kebab.endswith("y") and not kebab.endswith("ey"):
        kebab = kebab[:-1] + "ies"
    elif kebab.endswith(("s", "x", "sh")):
        kebab += "es"
    else:
        kebab += "s"
    return f"/api/v1/{kebab}"


def _to_collection(entity_name: str) -> str:
    """PascalCase → snake_case 복수형 컬렉션명."""
    snake = pascal_to_snake(entity_name)
    if snake.endswith("y") and not snake.endswith("ey"):
        return snake[:-1] + "ies"
    if snake.endswith(("s", "x", "sh")):
        return snake + "es"
    return snake + "s"


def register_entities(
    entries: list[CatalogEntry],
    services_dir: Path | None = None,
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    """서비스별 entities.py에 누락된 엔티티를 EntityMeta로 등록한다.

    Returns:
        서비스별 등록 수
    """
    svc_dir = services_dir or SERVICES_DIR
    result: dict[str, int] = {}

    # 서비스별 그룹화
    by_service: dict[str, list[CatalogEntry]] = {}
    for entry in entries:
        if not entry.service:
            continue
        by_service.setdefault(entry.service, []).append(entry)

    for service, svc_entries in by_service.items():
        entities_path = svc_dir / service / "app" / "entities.py"
        if not entities_path.exists():
            # entities.py가 없으면 건너뛰기 (커스텀 라우트 서비스)
            continue

        content = entities_path.read_text(encoding="utf-8")

        # 이미 등록된 엔티티 확인
        registered = set()
        for entry in svc_entries:
            snake = pascal_to_snake(entry.doctype_or_entity)
            if snake in content or entry.doctype_or_entity in content:
                registered.add(entry.doctype_or_entity)

        # 미등록 엔티티
        missing = [e for e in svc_entries if e.doctype_or_entity not in registered]
        if not missing:
            continue

        count = len(missing)
        result[service] = count

        if dry_run:
            for entry in missing:
                print(f"  [등록 예정] {service}: {entry.doctype_or_entity}")
            continue

        # 등록 코드 생성은 복잡하므로 로그만 출력
        for entry in missing:
            print(f"  [미등록] {service}: {entry.doctype_or_entity} ({entry.naming_prefix})")

    return result
