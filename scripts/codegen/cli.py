"""OneERP codegen CLI — CSV 카탈로그 기반 코드 검증 및 스캐폴딩."""

from __future__ import annotations

import argparse
import sys

from scripts.codegen.catalog import load_catalog
from scripts.codegen.generators.be_model import generate_be_model
from scripts.codegen.generators.fe_module import generate_fe_module
from scripts.codegen.validators.coverage import check_coverage, print_coverage_report
from scripts.codegen.validators.prefix_check import (
    check_duplicate_prefixes,
    check_empty_prefixes,
    print_prefix_report,
)
from scripts.codegen.validators.service_mapping import (
    check_service_mapping,
    print_service_mapping_report,
)


def _cmd_validate() -> int:
    """CSV ↔ 코드 정합성 검증을 실행한다."""
    entries = load_catalog()
    print(f"카탈로그 로드 완료: {len(entries)}개 엔티티\n")

    # 1. 커버리지 검증
    report = check_coverage(entries)
    print_coverage_report(report)
    print()

    # 2. prefix 중복 검사
    duplicates = check_duplicate_prefixes(entries)
    print_prefix_report(duplicates)

    empty_prefixes = check_empty_prefixes(entries)
    if empty_prefixes:
        print(f"\n[주의] naming_prefix 미설정 엔티티 ({len(empty_prefixes)}건):")
        for name in sorted(empty_prefixes):
            print(f"  - {name}")
    print()

    # 3. 서비스 매핑 검사
    missing_svcs, mismatches = check_service_mapping(entries)
    print_service_mapping_report(missing_svcs, mismatches)

    # 검증 결과 요약
    has_errors = bool(report.missing_p0_be or duplicates)
    if has_errors:
        print("\n[결과] 검증 실패 — 위 경고 사항을 확인하세요.")
        return 1
    print("\n[결과] 검증 통과")
    return 0


def _cmd_report() -> int:
    """커버리지 보고서를 출력한다."""
    entries = load_catalog()
    report = check_coverage(entries)
    print_coverage_report(report)

    # Phase별 통계
    phase_stats: dict[str, tuple[int, int]] = {}
    for entry in entries:
        phase = entry.phase or "?"
        total, impl = phase_stats.get(phase, (0, 0))
        phase_stats[phase] = (
            total + 1,
            impl + (1 if entry.doctype_or_entity not in report.missing_be else 0),
        )

    print("\n[Phase별 BE 구현 현황]")
    for phase in sorted(phase_stats):
        total, impl = phase_stats[phase]
        pct = impl / total * 100 if total else 0
        print(f"  {phase}: {impl}/{total} ({pct:.0f}%)")

    # 서비스별 통계
    svc_stats: dict[str, tuple[int, int]] = {}
    for entry in entries:
        svc = entry.service or "?"
        total, impl = svc_stats.get(svc, (0, 0))
        svc_stats[svc] = (
            total + 1,
            impl + (1 if entry.doctype_or_entity not in report.missing_be else 0),
        )

    print("\n[서비스별 BE 구현 현황]")
    for svc in sorted(svc_stats):
        total, impl = svc_stats[svc]
        pct = impl / total * 100 if total else 0
        print(f"  {svc}: {impl}/{total} ({pct:.0f}%)")

    return 0


def _cmd_generate(entity: str | None, phase: str | None) -> int:
    """스캐폴드를 생성한다."""
    entries = load_catalog()

    targets: list = []
    if entity:
        targets = [e for e in entries if e.doctype_or_entity == entity]
        if not targets:
            print(f"[오류] 엔티티 '{entity}'를 CSV에서 찾을 수 없습니다.")
            return 1
    elif phase:
        targets = [e for e in entries if e.phase == phase]
        if not targets:
            print(f"[오류] Phase '{phase}'에 해당하는 엔티티가 없습니다.")
            return 1
    else:
        print("[오류] --entity 또는 --phase 중 하나를 지정하세요.")
        return 1

    print(f"스캐폴드 생성 대상: {len(targets)}개 엔티티\n")

    be_count = 0
    fe_count = 0
    for entry in targets:
        if not entry.service:
            print(f"  [건너뜀] {entry.doctype_or_entity} (서비스 미지정)")
            continue

        print(f"--- {entry.doctype_or_entity} ({entry.service}) ---")
        be_path = generate_be_model(entry)
        if be_path:
            be_count += 1

        fe_path = generate_fe_module(entry)
        if fe_path:
            fe_count += 1

    print(f"\n[완료] BE 모델 {be_count}건, FE 모듈 {fe_count}건 생성")
    return 0


def main() -> None:
    """CLI 엔트리포인트."""
    parser = argparse.ArgumentParser(
        description="OneERP codegen 도구 — CSV 카탈로그 기반 코드 검증 및 스캐폴딩",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("validate", help="CSV ↔ 코드 정합성 검증")
    sub.add_parser("report", help="커버리지 보고서 출력")

    gen = sub.add_parser("generate", help="스캐폴드 생성")
    gen.add_argument("entity", nargs="?", help="생성할 엔티티명 (PascalCase)")
    gen.add_argument("--phase", help="Phase 기반 일괄 생성 (예: P1)")

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(_cmd_validate())
    elif args.command == "report":
        sys.exit(_cmd_report())
    elif args.command == "generate":
        sys.exit(_cmd_generate(args.entity, args.phase))
    else:
        parser.print_help()
        sys.exit(1)
