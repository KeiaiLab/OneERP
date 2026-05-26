"""판매송장(Sales Invoice) 리포지터리 접근 서비스.

OE002 대응: Route 에서 Repository 직접 인스턴스화 제거.
판매송장 + 전자세금계산서 두 Repository 에 대한 얇은 접근 계층을 제공한다.
비즈니스 로직(상태 전이, 세금 계산 등)은 Route layer 에 유지.
"""

from __future__ import annotations

from oneerp_core.repository import Repository


class SalesInvoiceRepoService:
    """판매송장 Route 에 주입되는 Repository 허브.

    sales_invoices + etax_invoices 두 컬렉션에 대해
    테넌트 스코프 Repository 를 보관한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self.invoices = Repository("sales_invoices", tenant_id=tenant_id)
        self.etax_invoices = Repository("etax_invoices", tenant_id=tenant_id)
