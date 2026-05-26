"""납품서(Delivery Note) 리포지터리 접근 서비스.

M3 arch-baseline 감소: Route 에서 Repository 직접 인스턴스화 제거 (최소 침습).
납품서/판매송장 두 Repository 에 대한 얇은 접근 계층만 제공한다.
비즈니스 로직(상태 전이, 단가 검증, 세금 계산 등)은 Route layer 에 유지.
"""

from __future__ import annotations

from oneerp_core.repository import Repository


class DeliveryNoteRepoService:
    """납품서 Route 에 주입되는 Repository 허브.

    delivery_notes + sales_invoices 두 컬렉션에 대한 테넌트 스코프
    Repository 를 보관한다. Route 는 `.notes` / `.invoices` 로 접근.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self.notes = Repository("delivery_notes", tenant_id=tenant_id)
        self.invoices = Repository("sales_invoices", tenant_id=tenant_id)
