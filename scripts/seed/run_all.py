"""전체 시드 실행 스크립트.

사용법:
    uv run python scripts/seed/run_all.py [--tenant TENANT_ID]

순서: currencies -> chart_of_accounts -> roles -> naming_series -> demo_data
"""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def main(tenant_id: str = "default") -> None:
    """전체 시드를 순서대로 실행한다."""
    # 지연 임포트 — DB 연결이 필요하므로 실행 시점에만 임포트
    from scripts.seed.seed_chart_of_accounts import seed as seed_coa
    from scripts.seed.seed_currencies import seed as seed_currencies
    from scripts.seed.seed_demo_data import seed as seed_demo
    from scripts.seed.seed_naming_series import seed as seed_naming
    from scripts.seed.seed_roles_permissions import seed as seed_roles

    logger.info("=== OneERP 시드 시작 (tenant: %s) ===", tenant_id)

    steps = [
        ("통화", seed_currencies),
        ("계정과목표", seed_coa),
        ("역할/권한", seed_roles),
        ("채번규칙", seed_naming),
        ("데모 데이터", seed_demo),
    ]

    total = 0
    for name, fn in steps:
        count = fn(tenant_id=tenant_id)
        logger.info("  [%s] %d개 삽입", name, count)
        total += count

    logger.info("=== OneERP 시드 완료: 총 %d개 삽입 ===", total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OneERP 시드 데이터 실행")
    parser.add_argument(
        "--tenant",
        default="default",
        help="테넌트 ID (기본: default)",
    )
    args = parser.parse_args()

    try:
        main(tenant_id=args.tenant)
    except Exception:
        logger.exception("시드 실행 중 오류 발생")
        sys.exit(1)
