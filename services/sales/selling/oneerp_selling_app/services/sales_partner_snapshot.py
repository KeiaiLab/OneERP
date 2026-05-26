"""판매 파트너 스냅샷 헬퍼."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from oneerp_core.repository import Repository

_CUSTOMER_COLLECTION = "customers"
_PARTNER_COLLECTION = "sales_partners"


def resolve_sales_partner_snapshot(tenant_id: str, customer_id: str | None) -> dict[str, Any]:
    """고객 현재 담당 판매 파트너를 거래 문서 스냅샷 형태로 반환한다."""
    if not customer_id:
        return {}

    customer = Repository(_CUSTOMER_COLLECTION, tenant_id=tenant_id).find_by_id(str(customer_id))
    if not customer:
        return {}

    partner_id = str(customer.get("sales_partner_id") or "").strip()
    if not partner_id:
        return {}

    partner = Repository(_PARTNER_COLLECTION, tenant_id=tenant_id).find_by_id(partner_id)
    partner_name = str(
        customer.get("sales_partner_name") or (partner.get("partner_name") if partner else "") or ""
    ).strip()
    commission_rate = Decimal(str((partner or {}).get("commission_rate", 0) or 0))
    return {
        "sales_partner_id": partner_id,
        "sales_partner_name": partner_name,
        "sales_partner_commission_rate": commission_rate,
    }
