"""판매주문(Sales Order) 리포지터리 접근 서비스.

OE002 대응: Route 에서 Repository 직접 인스턴스화 제거.
판매주문 + 후속 납품서/판매송장 Repository 3개에 대한 얇은 접근 계층을 제공한다.
복잡한 비즈니스 로직(상태 전이, 후속 문서 전환 등)은 Route layer 에 유지.
"""

from __future__ import annotations

from oneerp_core.repository import Repository


class SalesOrderRepoService:
    """판매주문 Route 에 주입되는 Repository 허브.

    sales_orders / delivery_notes / sales_invoices 세 컬렉션에 대해
    테넌트 스코프 Repository 를 보관한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self.orders = Repository("sales_orders", tenant_id=tenant_id)
        self.delivery_notes = Repository("delivery_notes", tenant_id=tenant_id)
        self.sales_invoices = Repository("sales_invoices", tenant_id=tenant_id)
