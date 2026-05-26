"""한국 표준 계정과목표 시드 — K-IFRS 기본 계정.

자산, 부채, 자본, 수익, 비용의 핵심 계정과목을 시드한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.config import get_core_settings
from oneerp_core.db import get_client

logger = logging.getLogger(__name__)

# K-IFRS 기본 계정과목표
ACCOUNTS: list[dict[str, Any]] = [
    # === 자산 (Asset) ===
    {"code": "1000", "name": "자산", "account_type": "asset", "is_group": True},
    {
        "code": "1100",
        "name": "유동자산",
        "account_type": "asset",
        "is_group": True,
        "parent": "1000",
    },
    {"code": "1110", "name": "현금및현금성자산", "account_type": "asset", "parent": "1100"},
    {"code": "1111", "name": "보통예금", "account_type": "asset", "parent": "1110"},
    {"code": "1112", "name": "당좌예금", "account_type": "asset", "parent": "1110"},
    {"code": "1120", "name": "단기금융상품", "account_type": "asset", "parent": "1100"},
    {"code": "1200", "name": "매출채권", "account_type": "asset", "parent": "1100"},
    {"code": "1210", "name": "받을어음", "account_type": "asset", "parent": "1200"},
    {"code": "1220", "name": "외상매출금", "account_type": "asset", "parent": "1200"},
    {"code": "1230", "name": "대손충당금", "account_type": "asset", "parent": "1200"},
    {"code": "1300", "name": "재고자산", "account_type": "asset", "parent": "1100"},
    {"code": "1310", "name": "상품", "account_type": "asset", "parent": "1300"},
    {"code": "1320", "name": "제품", "account_type": "asset", "parent": "1300"},
    {"code": "1330", "name": "원재료", "account_type": "asset", "parent": "1300"},
    {"code": "1340", "name": "재공품", "account_type": "asset", "parent": "1300"},
    {"code": "1400", "name": "기타유동자산", "account_type": "asset", "parent": "1100"},
    {"code": "1410", "name": "선급금", "account_type": "asset", "parent": "1400"},
    {"code": "1420", "name": "선급비용", "account_type": "asset", "parent": "1400"},
    {"code": "1430", "name": "미수금", "account_type": "asset", "parent": "1400"},
    {"code": "1440", "name": "부가세대급금", "account_type": "asset", "parent": "1400"},
    # 비유동자산
    {
        "code": "1500",
        "name": "비유동자산",
        "account_type": "asset",
        "is_group": True,
        "parent": "1000",
    },
    {"code": "1510", "name": "유형자산", "account_type": "asset", "parent": "1500"},
    {"code": "1511", "name": "토지", "account_type": "asset", "parent": "1510"},
    {"code": "1512", "name": "건물", "account_type": "asset", "parent": "1510"},
    {"code": "1513", "name": "기계장치", "account_type": "asset", "parent": "1510"},
    {"code": "1514", "name": "차량운반구", "account_type": "asset", "parent": "1510"},
    {"code": "1515", "name": "비품", "account_type": "asset", "parent": "1510"},
    {"code": "1516", "name": "감가상각누계액", "account_type": "asset", "parent": "1510"},
    {"code": "1520", "name": "무형자산", "account_type": "asset", "parent": "1500"},
    {"code": "1521", "name": "영업권", "account_type": "asset", "parent": "1520"},
    {"code": "1522", "name": "소프트웨어", "account_type": "asset", "parent": "1520"},
    # === 부채 (Liability) ===
    {"code": "2000", "name": "부채", "account_type": "liability", "is_group": True},
    {
        "code": "2100",
        "name": "유동부채",
        "account_type": "liability",
        "is_group": True,
        "parent": "2000",
    },
    {"code": "2110", "name": "매입채무", "account_type": "liability", "parent": "2100"},
    {"code": "2111", "name": "지급어음", "account_type": "liability", "parent": "2110"},
    {"code": "2112", "name": "외상매입금", "account_type": "liability", "parent": "2110"},
    {"code": "2120", "name": "미지급금", "account_type": "liability", "parent": "2100"},
    {"code": "2130", "name": "미지급급여", "account_type": "liability", "parent": "2100"},
    {"code": "2140", "name": "예수금", "account_type": "liability", "parent": "2100"},
    {"code": "2141", "name": "소득세예수금", "account_type": "liability", "parent": "2140"},
    {"code": "2142", "name": "지방소득세예수금", "account_type": "liability", "parent": "2140"},
    {"code": "2143", "name": "4대보험예수금", "account_type": "liability", "parent": "2140"},
    {"code": "2150", "name": "부가세예수금", "account_type": "liability", "parent": "2100"},
    {"code": "2160", "name": "선수금", "account_type": "liability", "parent": "2100"},
    {"code": "2170", "name": "단기차입금", "account_type": "liability", "parent": "2100"},
    {
        "code": "2200",
        "name": "비유동부채",
        "account_type": "liability",
        "is_group": True,
        "parent": "2000",
    },
    {"code": "2210", "name": "장기차입금", "account_type": "liability", "parent": "2200"},
    {"code": "2220", "name": "퇴직급여충당부채", "account_type": "liability", "parent": "2200"},
    # === 자본 (Equity) ===
    {"code": "3000", "name": "자본", "account_type": "equity", "is_group": True},
    {"code": "3100", "name": "자본금", "account_type": "equity", "parent": "3000"},
    {"code": "3200", "name": "자본잉여금", "account_type": "equity", "parent": "3000"},
    {"code": "3300", "name": "이익잉여금", "account_type": "equity", "parent": "3000"},
    {"code": "3310", "name": "이월이익잉여금", "account_type": "equity", "parent": "3300"},
    {"code": "3320", "name": "당기순이익", "account_type": "equity", "parent": "3300"},
    # === 수익 (Income) ===
    {"code": "4000", "name": "수익", "account_type": "income", "is_group": True},
    {"code": "4100", "name": "매출액", "account_type": "income", "parent": "4000"},
    {"code": "4110", "name": "상품매출", "account_type": "income", "parent": "4100"},
    {"code": "4120", "name": "제품매출", "account_type": "income", "parent": "4100"},
    {"code": "4130", "name": "용역매출", "account_type": "income", "parent": "4100"},
    {"code": "4200", "name": "매출할인", "account_type": "income", "parent": "4000"},
    {"code": "4300", "name": "영업외수익", "account_type": "income", "parent": "4000"},
    {"code": "4310", "name": "이자수익", "account_type": "income", "parent": "4300"},
    {"code": "4320", "name": "외환차익", "account_type": "income", "parent": "4300"},
    # === 비용 (Expense) ===
    {"code": "5000", "name": "비용", "account_type": "expense", "is_group": True},
    {"code": "5100", "name": "매출원가", "account_type": "expense", "parent": "5000"},
    {"code": "5110", "name": "상품매출원가", "account_type": "expense", "parent": "5100"},
    {"code": "5120", "name": "제품매출원가", "account_type": "expense", "parent": "5100"},
    {
        "code": "5200",
        "name": "판매비와관리비",
        "account_type": "expense",
        "is_group": True,
        "parent": "5000",
    },
    {"code": "5210", "name": "급여", "account_type": "expense", "parent": "5200"},
    {"code": "5220", "name": "퇴직급여", "account_type": "expense", "parent": "5200"},
    {"code": "5230", "name": "복리후생비", "account_type": "expense", "parent": "5200"},
    {"code": "5240", "name": "여비교통비", "account_type": "expense", "parent": "5200"},
    {"code": "5250", "name": "접대비", "account_type": "expense", "parent": "5200"},
    {"code": "5260", "name": "통신비", "account_type": "expense", "parent": "5200"},
    {"code": "5270", "name": "수도광열비", "account_type": "expense", "parent": "5200"},
    {"code": "5280", "name": "세금과공과", "account_type": "expense", "parent": "5200"},
    {"code": "5290", "name": "감가상각비", "account_type": "expense", "parent": "5200"},
    {"code": "5300", "name": "지급임차료", "account_type": "expense", "parent": "5200"},
    {"code": "5310", "name": "보험료", "account_type": "expense", "parent": "5200"},
    {"code": "5320", "name": "차량유지비", "account_type": "expense", "parent": "5200"},
    {"code": "5330", "name": "소모품비", "account_type": "expense", "parent": "5200"},
    {"code": "5340", "name": "지급수수료", "account_type": "expense", "parent": "5200"},
    {"code": "5400", "name": "영업외비용", "account_type": "expense", "parent": "5000"},
    {"code": "5410", "name": "이자비용", "account_type": "expense", "parent": "5400"},
    {"code": "5420", "name": "외환차손", "account_type": "expense", "parent": "5400"},
]


def seed(tenant_id: str = "default") -> int:
    """계정과목을 시드한다. 이미 존재하면 건너뛴다.

    Returns:
        새로 삽입한 계정 수.
    """
    settings = get_core_settings()
    client = get_client()
    db = client[settings.database_name]
    collection = db["accounts"]

    count = 0
    for acct in ACCOUNTS:
        # 멱등성: 동일 code + tenant_id가 있으면 건너뜀
        existing = collection.find_one(
            {"code": acct["code"], "tenant_id": tenant_id},
        )
        if existing:
            continue

        doc = {
            "_id": f"ACC-{acct['code']}",
            "tenant_id": tenant_id,
            "account_name": acct["name"],
            "account_type": acct["account_type"],
            "is_group": acct.get("is_group", False),
            "parent_account": acct.get("parent"),
            "currency": "KRW",
            "code": acct["code"],
            "docstatus": 0,
        }
        collection.insert_one(doc)
        count += 1

    logger.info("계정과목 시드 완료: %d개 삽입", count)
    return count
