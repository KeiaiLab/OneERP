#!/usr/bin/env python3
"""자산 감가상각 월말 배치 — G4-2 assets runbook 참조 스크립트.

매월 말일 02:00 실행. 각 자산의 잔존 내용연수 x 정액/정률 방식으로
감가상각비 계산 후 accounting 으로 journal 전기.

사용:
    uv run python scripts/migrations/assets/depreciation.py --period 2026-04 --apply
    uv run python scripts/migrations/assets/depreciation.py --period 2026-04 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal


def _connect():
    try:
        from pymongo import MongoClient
    except ImportError:
        print("pymongo 미설치", file=sys.stderr)
        sys.exit(2)
    uri = os.environ.get("ONEERP_FERRETDB_URI", "mongodb://localhost:27017/oneerp")
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def _compute_monthly(asset: dict) -> Decimal:
    """정액법: 취득가 / 내용연수(월)."""
    acq = Decimal(str(asset.get("acquisition_cost", 0)))
    life_months = int(asset.get("useful_life_months", 60))
    if life_months <= 0:
        return Decimal(0)
    return acq / Decimal(life_months)


def run(tenant: str, period: str, *, apply: bool) -> dict:
    client = _connect()
    db = client.get_default_database()
    assets = list(db.assets.find({"tenant_id": tenant, "status": "active"}))

    total = Decimal(0)
    processed = 0
    for asset in assets:
        # idempotency: 같은 period 에 이미 전기된 자산 skip.
        if db.asset_depreciation.find_one(
            {"asset_id": asset["_id"], "period": period, "tenant_id": tenant},
        ):
            continue
        monthly = _compute_monthly(asset)
        total += monthly
        processed += 1
        if apply:
            db.asset_depreciation.insert_one(
                {
                    "asset_id": asset["_id"],
                    "tenant_id": tenant,
                    "period": period,
                    "amount": str(monthly),
                    "method": "straight_line",
                },
            )
    return {
        "tenant": tenant,
        "period": period,
        "applied": apply,
        "processed": processed,
        "total_depreciation": str(total),
        "skipped_already_posted": len(assets) - processed,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="assets 감가상각 월말 배치")
    p.add_argument("--tenant", default=os.environ.get("ONEERP_TENANT", "default"))
    p.add_argument("--period", required=True, help="YYYY-MM")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    result = run(args.tenant, args.period, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
