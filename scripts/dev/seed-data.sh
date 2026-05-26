#!/usr/bin/env bash
# 개발용 시드 데이터 주입 — docker compose + BE 서비스 기동 후 실행
set -euo pipefail

export ONEERP_FERRETDB_URI="${ONEERP_FERRETDB_URI:-mongodb://localhost:27017}"
export ONEERP_DATABASE_NAME="${ONEERP_DATABASE_NAME:-oneerp}"
export ONEERP_DEV_ADMIN_USERNAME="${ONEERP_DEV_ADMIN_USERNAME:-demo}"
export ONEERP_DEV_ADMIN_PASSWORD="${ONEERP_DEV_ADMIN_PASSWORD:-demo1234}"

echo "시드 데이터 주입 중..."

uv run python - <<'PY'
from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime

from pymongo import MongoClient


def upsert_document(collection, identifier: dict, values: dict) -> None:
    collection.update_one(identifier, {"$set": values}, upsert=True)


client = MongoClient(os.environ["ONEERP_FERRETDB_URI"])
db = client[os.environ["ONEERP_DATABASE_NAME"]]
now = datetime.now(tz=UTC)
demo_username = os.environ["ONEERP_DEV_ADMIN_USERNAME"]
demo_password = os.environ["ONEERP_DEV_ADMIN_PASSWORD"]
password_hash = hashlib.sha256(demo_password.encode()).hexdigest()

upsert_document(
    db.tenants,
    {"_id": "default"},
    {
        "_id": "default",
        "tenant_id": "default",
        "tenant_name": "기본 테넌트",
        "name": "기본 테넌트",
        "plan": "enterprise",
        "allowed_modules": [
            "selling",
            "buying",
            "stock",
            "accounting",
            "hr",
            "payroll",
            "expenses",
            "crm",
            "assets",
            "projects",
            "quality",
            "analytics",
            "manufacturing",
            "rpa",
        ],
        "enabled_modules": [
            "selling",
            "buying",
            "stock",
            "accounting",
            "hr",
            "payroll",
            "expenses",
            "crm",
            "assets",
            "projects",
            "quality",
            "analytics",
            "manufacturing",
            "rpa",
        ],
        "is_active": True,
        "status": "active",
        "created_at": now,
    },
)

# 계약: 데모 관리자 계정은 {"username": "demo"} / password="demo1234" 로 고정
# 참조 테스트: tests/unit/test_deploy_generator.py::test_로컬_seed_계약은_demo_demo1234_로그인을_만든다
assert demo_username == "demo", "ONEERP_DEV_ADMIN_USERNAME 은 'demo' 여야 합니다"

upsert_document(
    db.users,
    {"username": demo_username},
    {
        "_id": demo_username,
        "username": demo_username,
        "tenant_id": "default",
        "email": f"{demo_username}@oneerp.local",
        "full_name": "데모 사용자",
        "roles": ["admin"],
        "user_tier": "super_admin",
        "is_super_admin": True,
        "is_active": True,
        "password_hash": password_hash,
        "created_at": now,
    },
)

upsert_document(
    db.companies,
    {"_id": "COMP-0001"},
    {
        "_id": "COMP-0001",
        "tenant_id": "default",
        "name": "OneERP 데모 주식회사",
        "country": "KR",
        "currency": "KRW",
        "default_currency": "KRW",
        "fiscal_year_start": "01-01",
        "created_at": now,
    },
)

upsert_document(
    db.warehouses,
    {"_id": "WH-MAIN"},
    {
        "_id": "WH-MAIN",
        "tenant_id": "default",
        "name": "본사 창고",
        "warehouse_type": "warehouse",
        "is_default": True,
        "created_at": now,
    },
)

upsert_document(
    db.sales_orders,
    {"_id": "SO-DEMO-202604"},
    {
        "_id": "SO-DEMO-202604",
        "tenant_id": "default",
        "docstatus": 1,
        "grand_total": 180000,
        "created_at": datetime(2026, 4, 2, tzinfo=UTC),
    },
)
upsert_document(
    db.sales_orders,
    {"_id": "SO-DEMO-202603"},
    {
        "_id": "SO-DEMO-202603",
        "tenant_id": "default",
        "docstatus": 1,
        "grand_total": 120000,
        "created_at": datetime(2026, 3, 12, tzinfo=UTC),
    },
)
upsert_document(
    db.accounts_receivable,
    {"_id": "AR-DEMO-001"},
    {
        "_id": "AR-DEMO-001",
        "tenant_id": "default",
        "status": "unpaid",
        "outstanding_amount": 30000,
    },
)
upsert_document(
    db.purchase_orders,
    {"_id": "PO-DEMO-001"},
    {
        "_id": "PO-DEMO-001",
        "tenant_id": "default",
        "docstatus": 0,
        "grand_total": 45000,
        "created_at": datetime(2026, 4, 3, tzinfo=UTC),
    },
)
upsert_document(
    db.stock_balances,
    {"_id": "STB-DEMO-LOW"},
    {
        "_id": "STB-DEMO-LOW",
        "tenant_id": "default",
        "is_low_stock": True,
    },
)
upsert_document(
    db.stock_balances,
    {"_id": "STB-DEMO-OK"},
    {
        "_id": "STB-DEMO-OK",
        "tenant_id": "default",
        "is_low_stock": False,
    },
)
upsert_document(
    db.stock_entries,
    {"_id": "STE-DEMO-OUT"},
    {
        "_id": "STE-DEMO-OUT",
        "tenant_id": "default",
        "entry_type": "outgoing",
    },
)
upsert_document(
    db.approval_requests,
    {"_id": "APR-DEMO-001"},
    {
        "_id": "APR-DEMO-001",
        "tenant_id": "default",
        "title": "데모 구매 승인",
        "requester_name": "데모 사용자",
        "document_type": "purchase_order",
        "status": "pending",
        "current_approver": "demo",
        "created_at": now,
    },
)
upsert_document(
    db.employees,
    {"_id": "EMP-DEMO-001"},
    {
        "_id": "EMP-DEMO-001",
        "tenant_id": "default",
        "is_active": True,
    },
)
upsert_document(
    db.salary_slips,
    {"_id": "SLIP-DEMO-001"},
    {
        "_id": "SLIP-DEMO-001",
        "tenant_id": "default",
        "docstatus": 1,
        "net_pay": 4200000,
        "created_at": datetime(2026, 4, 1, tzinfo=UTC),
    },
)

print("시드 데이터 주입 완료")
client.close()
PY

echo "[oneerp-dev] demo credentials: ${ONEERP_DEV_ADMIN_USERNAME} / ${ONEERP_DEV_ADMIN_PASSWORD}"
