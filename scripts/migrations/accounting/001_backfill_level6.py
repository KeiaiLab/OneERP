#!/usr/bin/env python3
"""Accounting Chart-of-Accounts level 6 → level 5 백필 마이그레이션 (2026-04).

배경:
    v18 에서 계정 트리를 6단계로 확장했다가 drift 발견 후 5단계로 환원.
    기존 level-6 데이터를 상위 level-5 코드에 병합하면서 원장 금액은 보존.

사용:
    uv run python scripts/migrations/accounting/001_backfill_level6.py \
        --tenant default --dry-run
    uv run python scripts/migrations/accounting/001_backfill_level6.py \
        --tenant default --apply --checkpoint docs/kb/incident/INC-2026-04-21-accounting-v18-validation.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _connect():
    try:
        from pymongo import MongoClient
    except ImportError:
        print("pymongo 미설치", file=sys.stderr)
        sys.exit(2)
    uri = os.environ.get("ONEERP_FERRETDB_URI", "mongodb://localhost:27017/oneerp")
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def level_of(code: str) -> int:
    """계정 코드의 level = 세그먼트 수 (점 구분)."""
    return code.count(".") + 1


def parent_code(code: str) -> str:
    """level 6 → 5 의 상위 코드. 가장 마지막 세그먼트 제거."""
    return code.rsplit(".", 1)[0]


def migrate(tenant: str, *, apply: bool) -> dict:
    client = _connect()
    db = client.get_default_database()

    # 영향 받는 journal_entries 찾기.
    level6 = list(
        db.journal_entries.find(
            {"tenant_id": tenant, "account_code": {"$regex": r"^[0-9]+(\.[0-9]+){5}$"}}
        ),
    )
    moved: list[dict] = []
    for je in level6:
        old = je["account_code"]
        new = parent_code(old)
        moved.append({"_id": str(je["_id"]), "old": old, "new": new})
        if apply:
            db.journal_entries.update_one(
                {"_id": je["_id"]},
                {
                    "$set": {"account_code": new},
                    "$push": {
                        "migration_trail": {
                            "from": old,
                            "to": new,
                            "script": "001_backfill_level6.py",
                        }
                    },
                },
            )

    # chart_of_accounts 에서 level 6 노드 soft-delete.
    removed_accounts = 0
    if apply:
        res = db.chart_of_accounts.update_many(
            {"tenant_id": tenant, "code": {"$regex": r"^[0-9]+(\.[0-9]+){5}$"}},
            {
                "$set": {
                    "deprecated": True,
                    "deprecated_at": __import__("datetime").datetime.utcnow(),
                }
            },
        )
        removed_accounts = res.modified_count

    return {
        "tenant": tenant,
        "applied": apply,
        "moved_entries": len(moved),
        "deprecated_accounts": removed_accounts,
        "sample": moved[:5],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="level 6 → 5 백필")
    p.add_argument("--tenant", default=os.environ.get("ONEERP_TENANT", "default"))
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    p.add_argument("--checkpoint", help="포스트모템 문서 경로 (apply 시 무결성 증빙으로 참조)")
    args = p.parse_args()

    if args.apply and args.checkpoint and not Path(args.checkpoint).is_file():
        print(f"ERROR: --checkpoint 파일 없음: {args.checkpoint}", file=sys.stderr)
        return 2

    result = migrate(args.tenant, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
