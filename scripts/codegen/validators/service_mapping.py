"""CSV service 컬럼 ↔ 실제 서비스 디렉토리 검증."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.codegen.catalog import SERVICES_DIR

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from scripts.codegen.catalog import CatalogEntry


def _scan_service_dirs(services_dir: Path) -> set[str]:
    """실제 존재하는 서비스 디렉토리 이름 집합을 반환한다."""
    if not services_dir.is_dir():
        return set()
    return {d.name for d in sorted(services_dir.iterdir()) if d.is_dir() and (d / "app").is_dir()}


def check_service_mapping(
    entries: Sequence[CatalogEntry],
    services_dir: Path | None = None,
) -> tuple[set[str], list[tuple[str, str]]]:
    """CSV의 service 컬럼과 실제 서비스 디렉토리를 대조한다.

    반환:
        (존재하지 않는 서비스 집합, [(엔티티명, 잘못된 서비스명), ...])
    """
    svc_dir = services_dir or SERVICES_DIR
    actual_services = _scan_service_dirs(svc_dir)

    # CSV에서 참조하는 서비스 중 존재하지 않는 것
    csv_services = {e.service for e in entries if e.service}
    missing_services = csv_services - actual_services

    # 존재하지 않는 서비스를 참조하는 엔티티 목록
    mismatches = [
        (entry.doctype_or_entity, entry.service)
        for entry in entries
        if entry.service and entry.service not in actual_services
    ]

    return missing_services, mismatches


def print_service_mapping_report(
    missing_services: set[str],
    mismatches: list[tuple[str, str]],
) -> None:
    """서비스 매핑 보고서를 콘솔에 출력한다."""
    if not missing_services:
        print("[OK] 모든 CSV 서비스 디렉토리가 존재합니다.")
        return

    print(f"[경고] 존재하지 않는 서비스 ({len(missing_services)}건):")
    for svc in sorted(missing_services):
        print(f"  - {svc}")

    if mismatches:
        print(f"\n[경고] 매핑 불일치 엔티티 ({len(mismatches)}건):")
        for entity, service in sorted(mismatches):
            print(f"  - {entity} → {service} (디렉토리 없음)")
