#!/usr/bin/env python3
"""문서 커버리지 보고서 — 코드 엔티티 vs 모듈 명세 교차 대조."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def count_code_entities() -> dict[str, int]:
    """서비스별 BaseDocument 상속 모델 수를 반환한다."""
    counts: dict[str, int] = {}
    for svc_dir in sorted((ROOT / "services").iterdir()):
        if not svc_dir.is_dir():
            continue
        models_dir = svc_dir / "app" / "models"
        if not models_dir.exists():
            continue
        model_count = sum(1 for f in models_dir.glob("*.py") if not f.name.startswith("_"))
        counts[svc_dir.name] = model_count
    return counts


def count_catalog_entities() -> int:
    """01-module-catalog.csv에서 엔티티 수를 반환한다."""
    csv_path = ROOT / "docs" / "product" / "scope" / "01-module-catalog.csv"
    if not csv_path.exists():
        return 0
    with csv_path.open() as f:
        reader = csv.reader(f)
        next(reader, None)  # 헤더 스킵
        return sum(1 for _ in reader)


def main() -> None:
    """커버리지 보고서를 출력한다."""
    code_entities = count_code_entities()
    catalog_count = count_catalog_entities()

    total_code = sum(code_entities.values())
    coverage = (total_code / catalog_count * 100) if catalog_count > 0 else 0

    print("=== 문서 커버리지 보고서 ===\n")
    print(f"카탈로그 엔티티: {catalog_count}개")
    print(f"코드 엔티티: {total_code}개")
    print(f"커버리지: {coverage:.1f}%\n")

    print("서비스별 모델 수:")
    for svc, count in sorted(code_entities.items()):
        print(f"  {svc}: {count}개")

    if coverage < 80:
        print(f"\nWARN: 커버리지 {coverage:.1f}% < 80% 임계치")
        sys.exit(1)
    else:
        print(f"\n커버리지 {coverage:.1f}% >= 80% 통과")


if __name__ == "__main__":
    main()
