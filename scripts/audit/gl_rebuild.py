#!/usr/bin/env python3
"""account_balance 재집계 도구 — G4-5 accounting drift P2 대응에서 사용.

gl_integrity.py 가 `balance_reconcile` 불일치를 발견하면, 이 도구로
journal_entries 를 시작으로 account_balances 를 권위있는 값으로 재구성한다.

사용:
    uv run python scripts/audit/gl_rebuild.py --tenant default --period 2026-04 --apply
    uv run python scripts/audit/gl_rebuild.py --tenant default --period 2026-04 --dry-run

종료 코드:
  0 — 재집계 완료 (불일치 없거나 --apply 로 해소)
  1 — --dry-run 으로 불일치 검출, 재적용은 안 함
  2 — 환경 오류
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from decimal import Decimal

logger = logging.getLogger("gl_rebuild")


def _connect():
    try:
        from pymongo import MongoClient
    except ImportError:
        print("pymongo 미설치. `uv add pymongo` 후 재실행.", file=sys.stderr)
        sys.exit(2)
    uri = os.environ.get("ONEERP_FERRETDB_URI", "mongodb://localhost:27017/oneerp")
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def compute_balances(db, tenant: str, period: str) -> dict[str, Decimal]:
    """journal_entries 로부터 계정별 잔액 재계산."""
    agg: dict[str, Decimal] = {}
    for je in db.journal_entries.find({"tenant_id": tenant, "period": period}):
        code = je["account_code"]
        agg.setdefault(code, Decimal(0))
        agg[code] += Decimal(str(je.get("debit", 0))) - Decimal(str(je.get("credit", 0)))
    return agg


def rebuild(
    tenant: str, period: str, *, apply: bool
) -> tuple[int, dict[str, Decimal], dict[str, Decimal]]:
    client = _connect()
    db = client.get_default_database()
    want = compute_balances(db, tenant, period)
    stored = {
        b["account_code"]: Decimal(str(b.get("balance", 0)))
        for b in db.account_balances.find({"tenant_id": tenant, "period": period})
    }
    diff = {
        code: want[code] - stored.get(code, Decimal(0))
        for code in want
        if want[code] != stored.get(code, Decimal(0))
    }
    if not diff:
        return 0, want, stored
    if not apply:
        return len(diff), want, stored
    # 재적용 — upsert 로 원장 값 덮어쓰기. created_at 보존.
    for code, value in want.items():
        db.account_balances.update_one(
            {"tenant_id": tenant, "period": period, "account_code": code},
            {"$set": {"balance": str(value), "rebuilt_by": "gl_rebuild.py"}},
            upsert=True,
        )
    return 0, want, stored


def main() -> int:
    p = argparse.ArgumentParser(description="account_balance 재집계")
    p.add_argument("--tenant", default=os.environ.get("ONEERP_TENANT", "default"))
    p.add_argument("--period", required=True, help="YYYY-MM")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true", help="불일치 해소 적용")
    g.add_argument("--dry-run", action="store_true", help="불일치만 보고 (종료 1 if drift)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    rc, want, stored = rebuild(args.tenant, args.period, apply=args.apply)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "tenant": args.tenant,
                    "period": args.period,
                    "applied": args.apply,
                    "recomputed_accounts": len(want),
                    "stored_accounts": len(stored),
                    "drift_accounts": rc,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    else:
        action = "applied" if args.apply else "dry-run"
        print(f"{action}: tenant={args.tenant} period={args.period} drift_accounts={rc}")
        print(f"  recomputed={len(want)} accounts, stored={len(stored)} accounts")

    return rc if args.dry_run else 0


if __name__ == "__main__":
    raise SystemExit(main())
