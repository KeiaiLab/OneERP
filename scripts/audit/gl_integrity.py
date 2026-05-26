#!/usr/bin/env python3
"""GL(총계정원장) 무결성 검증 도구 — G4-3 accounting 복구 드릴 전용.

검증 항목 (ADR-0009 회계 무결성 정의):
  1. 차변 합계 = 대변 합계 (journal_entries)
  2. 계정별 account_balance 가 journal_entries 재집계와 일치
  3. 마감 기간(period.closed) 이후 journal 추가/수정이 없음

사용:
    uv run python scripts/audit/gl_integrity.py --period 2026-04 --strict
    uv run python scripts/audit/gl_integrity.py --tenant default --period 2026-04 --format json

종료 코드:
  0 — 무결성 통과
  1 — 불일치 발견 (상세는 stdout / stderr)
  2 — 환경 오류(DB 연결 실패, 인자 누락)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class IntegrityFinding:
    check: str
    severity: str
    detail: str
    delta: Decimal | None = None


@dataclass
class IntegrityReport:
    tenant: str
    period: str
    findings: list[IntegrityFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)


def _connect():
    """FerretDB 클라이언트 반환. pymongo 미설치 시 명확한 오류로 종료."""
    try:
        from pymongo import MongoClient
    except ImportError:
        print("pymongo 미설치. `uv add pymongo` 후 재실행.", file=sys.stderr)
        sys.exit(2)
    uri = os.environ.get("ONEERP_FERRETDB_URI", "mongodb://localhost:27017/oneerp")
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def check_journal_balance(db, tenant: str, period: str) -> IntegrityFinding | None:
    """차변·대변 합계 일치 확인."""
    pipeline = [
        {"$match": {"tenant_id": tenant, "period": period}},
        {"$group": {"_id": None, "debit": {"$sum": "$debit"}, "credit": {"$sum": "$credit"}}},
    ]
    agg = list(db.journal_entries.aggregate(pipeline))
    if not agg:
        return IntegrityFinding(
            check="journal_balance",
            severity="warning",
            detail=f"no entries for {tenant}/{period}",
        )
    row = agg[0]
    d, c = Decimal(str(row["debit"])), Decimal(str(row["credit"]))
    if d != c:
        return IntegrityFinding(
            check="journal_balance",
            severity="error",
            detail=f"debit {d} != credit {c}",
            delta=d - c,
        )
    return None


def check_balance_reconcile(db, tenant: str, period: str) -> list[IntegrityFinding]:
    """account_balance 가 journal 재집계와 일치하는지."""
    stored = {
        (b["account_code"]): Decimal(str(b.get("balance", 0)))
        for b in db.account_balances.find({"tenant_id": tenant, "period": period})
    }
    recomputed: dict[str, Decimal] = {}
    for je in db.journal_entries.find({"tenant_id": tenant, "period": period}):
        code = je["account_code"]
        recomputed.setdefault(code, Decimal(0))
        recomputed[code] += Decimal(str(je.get("debit", 0))) - Decimal(str(je.get("credit", 0)))
    findings: list[IntegrityFinding] = []
    for code, want in recomputed.items():
        have = stored.get(code, Decimal(0))
        if have != want:
            findings.append(
                IntegrityFinding(
                    check=f"balance_reconcile[{code}]",
                    severity="error",
                    detail=f"stored {have} != recomputed {want}",
                    delta=have - want,
                ),
            )
    return findings


def check_closed_period_seal(db, tenant: str, period: str) -> IntegrityFinding | None:
    """마감 이후 이벤트가 있는지."""
    closed = db.periods.find_one({"tenant_id": tenant, "period": period, "state": "closed"})
    if not closed:
        return None
    closed_at = closed.get("closed_at")
    if closed_at is None:
        return None
    post = db.journal_entries.count_documents(
        {"tenant_id": tenant, "period": period, "created_at": {"$gt": closed_at}},
    )
    if post:
        return IntegrityFinding(
            check="closed_period_seal",
            severity="error",
            detail=f"{post} entries after period close at {closed_at}",
        )
    return None


def run(tenant: str, period: str) -> IntegrityReport:
    client = _connect()
    db = client.get_default_database()
    rep = IntegrityReport(tenant=tenant, period=period)
    if (f := check_journal_balance(db, tenant, period)) is not None:
        rep.findings.append(f)
    rep.findings.extend(check_balance_reconcile(db, tenant, period))
    if (f := check_closed_period_seal(db, tenant, period)) is not None:
        rep.findings.append(f)
    return rep


def main() -> int:
    p = argparse.ArgumentParser(description="GL 무결성 검증 (ADR-0009)")
    p.add_argument("--tenant", default=os.environ.get("ONEERP_TENANT", "default"))
    p.add_argument("--period", required=True, help="YYYY-MM")
    p.add_argument("--strict", action="store_true", help="warning 도 실패로 간주")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    rep = run(args.tenant, args.period)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "tenant": rep.tenant,
                    "period": rep.period,
                    "ok": rep.ok,
                    "findings": [
                        {
                            "check": f.check,
                            "severity": f.severity,
                            "detail": f.detail,
                            "delta": str(f.delta) if f.delta is not None else None,
                        }
                        for f in rep.findings
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    else:
        print(f"tenant={rep.tenant} period={rep.period} ok={rep.ok}")
        for f in rep.findings:
            print(f"  [{f.severity:7s}] {f.check}: {f.detail}")

    if not rep.ok:
        return 1
    if args.strict and any(f.severity == "warning" for f in rep.findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
