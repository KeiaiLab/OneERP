"""데모용 샘플 데이터 시드 — 고객, 공급사, 품목, 사용자.

개발/데모 환경에서 즉시 확인할 수 있는 최소 데이터를 시드한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.config import get_core_settings
from oneerp_core.db import get_client

logger = logging.getLogger(__name__)

CUSTOMERS: list[dict[str, Any]] = [
    {"code": "CUST-001", "name": "한국전자(주)", "group": "대기업", "territory": "서울"},
    {"code": "CUST-002", "name": "삼성물산(주)", "group": "대기업", "territory": "서울"},
    {"code": "CUST-003", "name": "(주)현대모비스", "group": "대기업", "territory": "경기"},
    {"code": "CUST-004", "name": "(주)테크솔루션", "group": "중소기업", "territory": "부산"},
    {"code": "CUST-005", "name": "스마트커머스(주)", "group": "중소기업", "territory": "대구"},
]

SUPPLIERS: list[dict[str, Any]] = [
    {"code": "SUP-001", "name": "(주)원자재공급", "group": "원자재", "country": "KR"},
    {"code": "SUP-002", "name": "글로벌파츠 코리아", "group": "부품", "country": "KR"},
    {"code": "SUP-003", "name": "Shenzhen Parts Co.", "group": "부품", "country": "CN"},
    {"code": "SUP-004", "name": "일본정밀(주)", "group": "정밀부품", "country": "JP"},
    {"code": "SUP-005", "name": "(주)포장재센터", "group": "포장", "country": "KR"},
]

ITEMS: list[dict[str, Any]] = [
    {"code": "ITEM-001", "name": "노트북 15인치", "group": "완제품", "uom": "EA", "rate": 1500000},
    {"code": "ITEM-002", "name": "무선마우스", "group": "완제품", "uom": "EA", "rate": 35000},
    {"code": "ITEM-003", "name": "USB-C 케이블", "group": "부자재", "uom": "EA", "rate": 5000},
    {
        "code": "ITEM-004",
        "name": "LCD 패널 15.6인치",
        "group": "원자재",
        "uom": "EA",
        "rate": 250000,
    },
    {"code": "ITEM-005", "name": "SSD 512GB", "group": "원자재", "uom": "EA", "rate": 80000},
    {"code": "ITEM-006", "name": "RAM DDR5 16GB", "group": "원자재", "uom": "EA", "rate": 60000},
    {
        "code": "ITEM-007",
        "name": "배터리 셀 4000mAh",
        "group": "원자재",
        "uom": "EA",
        "rate": 45000,
    },
    {"code": "ITEM-008", "name": "포장박스 (대)", "group": "포장", "uom": "EA", "rate": 2000},
    {
        "code": "ITEM-009",
        "name": "서비스 유지보수 (월)",
        "group": "서비스",
        "uom": "월",
        "rate": 500000,
    },
    {
        "code": "ITEM-010",
        "name": "소프트웨어 라이선스",
        "group": "서비스",
        "uom": "EA",
        "rate": 300000,
    },
]

DEMO_USERS: list[dict[str, Any]] = [
    {
        "username": "admin",
        "full_name": "시스템 관리자",
        "email": "admin@oneerp.local",
        "role": "System Manager",
    },
    {
        "username": "sales01",
        "full_name": "김영업",
        "email": "sales01@oneerp.local",
        "role": "Sales User",
    },
    {
        "username": "purchase01",
        "full_name": "이구매",
        "email": "purchase01@oneerp.local",
        "role": "Purchase User",
    },
    {
        "username": "accountant01",
        "full_name": "박회계",
        "email": "accountant01@oneerp.local",
        "role": "Accounts User",
    },
]


def _seed_collection(
    db: Any,
    collection_name: str,
    items: list[dict[str, Any]],
    id_field: str,
    tenant_id: str,
) -> int:
    """범용 시드 헬퍼 — 지정 컬렉션에 멱등하게 삽입한다."""
    col = db[collection_name]
    count = 0
    for item in items:
        doc_id = item[id_field]
        existing = col.find_one({"_id": doc_id, "tenant_id": tenant_id})
        if existing:
            continue
        doc = {**item, "_id": doc_id, "tenant_id": tenant_id, "docstatus": 0}
        col.insert_one(doc)
        count += 1
    return count


def seed(tenant_id: str = "default") -> int:
    """데모 데이터를 시드한다. 이미 존재하면 건너뛴다.

    Returns:
        새로 삽입한 총 문서 수.
    """
    settings = get_core_settings()
    client = get_client()
    db = client[settings.database_name]

    total = 0

    # 고객
    total += _seed_collection(db, "customers", CUSTOMERS, "code", tenant_id)

    # 공급사
    total += _seed_collection(db, "suppliers", SUPPLIERS, "code", tenant_id)

    # 품목
    total += _seed_collection(db, "items", ITEMS, "code", tenant_id)

    # 데모 사용자
    total += _seed_collection(db, "users", DEMO_USERS, "username", tenant_id)

    logger.info("데모 데이터 시드 완료: 총 %d개 삽입", total)
    return total
