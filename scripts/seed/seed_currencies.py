"""통화 마스터 시드 — 기본 4개 통화.

KRW, USD, EUR, JPY를 시드한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.config import get_core_settings
from oneerp_core.db import get_client

logger = logging.getLogger(__name__)

CURRENCIES: list[dict[str, Any]] = [
    {
        "code": "KRW",
        "name": "대한민국 원",
        "symbol": "₩",
        "fraction": "전",
        "fraction_units": 1,
        "is_enabled": True,
    },
    {
        "code": "USD",
        "name": "미국 달러",
        "symbol": "$",
        "fraction": "센트",
        "fraction_units": 100,
        "is_enabled": True,
    },
    {
        "code": "EUR",
        "name": "유로",
        "symbol": "€",
        "fraction": "센트",
        "fraction_units": 100,
        "is_enabled": True,
    },
    {
        "code": "JPY",
        "name": "일본 엔",
        "symbol": "¥",
        "fraction": "전",
        "fraction_units": 1,
        "is_enabled": True,
    },
]


def seed(tenant_id: str = "default") -> int:
    """통화를 시드한다. 이미 존재하면 건너뛴다.

    Returns:
        새로 삽입한 통화 수.
    """
    settings = get_core_settings()
    client = get_client()
    db = client[settings.database_name]
    collection = db["currencies"]

    count = 0
    for cur in CURRENCIES:
        existing = collection.find_one(
            {"currency_code": cur["code"], "tenant_id": tenant_id},
        )
        if existing:
            continue

        doc = {
            "_id": f"CUR-{cur['code']}",
            "tenant_id": tenant_id,
            "currency_code": cur["code"],
            "currency_name": cur["name"],
            "symbol": cur["symbol"],
            "fraction": cur["fraction"],
            "fraction_units": cur["fraction_units"],
            "is_enabled": cur["is_enabled"],
            "docstatus": 0,
        }
        collection.insert_one(doc)
        count += 1

    logger.info("통화 시드 완료: %d개 삽입", count)
    return count
