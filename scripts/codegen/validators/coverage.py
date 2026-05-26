"""CSV ↔ BE 모델 커버리지 검증."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from scripts.codegen.catalog import FE_MODULES_DIR, SERVICES_DIR, load_aliases
from scripts.codegen.naming import pascal_to_snake

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from scripts.codegen.catalog import CatalogEntry


@dataclass(slots=True)
class CoverageReport:
    """커버리지 분석 결과."""

    total: int = 0
    implemented_be: int = 0
    implemented_fe: int = 0
    missing_be: list[str] = field(default_factory=list)
    missing_fe: list[str] = field(default_factory=list)
    missing_p0_be: list[str] = field(default_factory=list)
    orphan_be: list[str] = field(default_factory=list)
    orphan_fe: list[str] = field(default_factory=list)


def _scan_be_models(services_dir: Path) -> dict[str, str]:
    """BE 모델 파일을 스캔하여 {모델파일명(확장자없음): 서비스명} 매핑을 반환한다."""
    models: dict[str, str] = {}
    for service_dir in sorted(services_dir.iterdir()):
        models_dir = service_dir / "app" / "models"
        if not models_dir.is_dir():
            continue
        for py_file in sorted(models_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            models[py_file.stem] = service_dir.name
    return models


def _scan_fe_modules(fe_dir: Path) -> set[str]:
    """FE 모듈 파일을 스캔하여 모듈 파일명 집합을 반환한다 (확장자 제외)."""
    if not fe_dir.is_dir():
        return set()
    return {f.stem for f in sorted(fe_dir.glob("*.ts"))}


def _resolve_model_filename(
    entity_name: str,
    aliases: dict[str, str],
) -> str:
    """CSV 엔티티명을 실제 BE 모델 파일명(확장자 없음)으로 변환한다."""
    if entity_name in aliases:
        return aliases[entity_name]
    return pascal_to_snake(entity_name)


def _resolve_fe_filename(entity_name: str) -> str:
    """CSV 엔티티명을 FE 모듈 파일명(확장자 없음)으로 변환한다.

    PascalCase → kebab-case 복수형.
    예시: GeneralLedgerEntry → general-ledger-entries
    """
    snake = pascal_to_snake(entity_name)
    kebab = snake.replace("_", "-")
    # 간단한 복수형 처리
    if kebab.endswith("y") and not kebab.endswith("ey"):
        kebab = kebab[:-1] + "ies"
    elif kebab.endswith(("s", "x", "sh")):
        kebab += "es"
    else:
        kebab += "s"
    return kebab


def check_coverage(
    entries: Sequence[CatalogEntry],
    services_dir: Path | None = None,
    fe_dir: Path | None = None,
) -> CoverageReport:
    """CSV 엔트리와 실제 코드 간 커버리지를 분석한다."""
    svc_dir = services_dir or SERVICES_DIR
    fe_modules_dir = fe_dir or FE_MODULES_DIR
    aliases = load_aliases()

    be_models = _scan_be_models(svc_dir)
    fe_modules = _scan_fe_modules(fe_modules_dir)

    report = CoverageReport(total=len(entries))

    # CSV에 있는 엔티티 중 코드에 없는 것 찾기
    expected_be_files: dict[str, str] = {}  # {모델파일명: 엔티티명}
    expected_fe_files: dict[str, str] = {}  # {FE파일명: 엔티티명}

    for entry in entries:
        be_file = _resolve_model_filename(entry.doctype_or_entity, aliases)
        fe_file = _resolve_fe_filename(entry.doctype_or_entity)
        expected_be_files[be_file] = entry.doctype_or_entity
        expected_fe_files[fe_file] = entry.doctype_or_entity

        if be_file in be_models:
            report.implemented_be += 1
        else:
            report.missing_be.append(entry.doctype_or_entity)
            if entry.is_p0:
                report.missing_p0_be.append(entry.doctype_or_entity)

        if fe_file in fe_modules:
            report.implemented_fe += 1
        else:
            report.missing_fe.append(entry.doctype_or_entity)

    # 코드에 있지만 CSV에 없는 것 찾기 (orphan)
    for model_file in be_models:
        if model_file not in expected_be_files:
            report.orphan_be.append(model_file)

    for fe_file in fe_modules:
        if fe_file not in expected_fe_files:
            report.orphan_fe.append(fe_file)

    return report


def print_coverage_report(report: CoverageReport) -> None:
    """커버리지 보고서를 콘솔에 출력한다."""
    print("=" * 60)
    print("  OneERP 커버리지 보고서")
    print("=" * 60)
    print()

    # BE 커버리지
    be_pct = (report.implemented_be / report.total * 100) if report.total else 0
    print(f"[BE 모델] {report.implemented_be}/{report.total} ({be_pct:.1f}%)")

    # FE 커버리지
    fe_pct = (report.implemented_fe / report.total * 100) if report.total else 0
    print(f"[FE 모듈] {report.implemented_fe}/{report.total} ({fe_pct:.1f}%)")
    print()

    # 미구현 P0 엔티티
    if report.missing_p0_be:
        print(f"[경고] 미구현 P0 BE 엔티티 ({len(report.missing_p0_be)}건):")
        for name in sorted(report.missing_p0_be):
            print(f"  - {name}")
        print()

    # 미구현 BE 전체
    if report.missing_be:
        print(f"[정보] 미구현 BE 엔티티 ({len(report.missing_be)}건):")
        for name in sorted(report.missing_be):
            print(f"  - {name}")
        print()

    # Orphan BE
    if report.orphan_be:
        print(f"[주의] CSV에 없는 BE 모델 ({len(report.orphan_be)}건):")
        for name in sorted(report.orphan_be):
            print(f"  - {name}")
        print()

    # Orphan FE
    if report.orphan_fe:
        print(f"[주의] CSV에 없는 FE 모듈 ({len(report.orphan_fe)}건):")
        for name in sorted(report.orphan_fe):
            print(f"  - {name}")
        print()

    print("=" * 60)
