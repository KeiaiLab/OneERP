"""전자세금계산서(etax) 서비스 — routes/sales_invoices.py 경계 위반 제거.

M1-3 도입 목적 (원칙 P2):
- `routes/sales_invoices.py` 의 `_ensure_etax_invoice_ref` / `_build_etax_summary`
  이 Route 파일에서 Repository(etax_repo) 를 직접 호출하는 **계층 경계 위반**
  을 service 층으로 이동.
- Route → Service → Repository 3층 강제 원칙의 selling 파일럿 표본.

M1-3 에서는 **서비스 클래스 골격**만 준비한다. 실제 로직 이관 및 route
호출부 교체는 M2 selling 파일럿에서 수행. 이렇게 분리하면 이전 세션의
routes/sales_invoices.py 수정본과 충돌 없이 추가 가능.
"""

from __future__ import annotations

from typing import Any

from oneerp_core.service_base import DomainService


class EtaxInvoiceService(DomainService):
    """전자세금계산서 도메인 서비스 (M1-3 골격).

    예상 API (M2 에서 구현 완료):
        def ensure_ref(self, invoice_id: str) -> str: ...
        def build_summary(self, invoice_id: str) -> dict: ...

    사용 예 (M2 이후):
        svc = EtaxInvoiceService(tenant_id=current_tenant)
        svc.register_repo("sales_invoice", sales_invoice_repo)
        svc.register_repo("etax_invoice", etax_repo)
        ref = svc.ensure_ref(invoice_id)
    """

    REPO_SALES_INVOICE = "sales_invoice"
    REPO_ETAX = "etax_invoice"

    def ensure_ref(self, invoice_id: str) -> str:
        """송장에 전자세금계산서 레퍼런스를 보장.

        M1-3 에서는 NotImplementedError — M2 에서 routes/sales_invoices.py 의
        _ensure_etax_invoice_ref 로직을 이곳으로 이관 + 호출부 교체.
        """
        raise NotImplementedError(
            "ensure_ref 는 M2 selling 파일럿에서 구현됩니다 "
            "(routes/sales_invoices.py:_ensure_etax_invoice_ref 이관 예정)."
        )

    def build_summary(self, invoice_id: str) -> dict[str, Any]:
        """송장-전자세금계산서 요약 dict 반환 (M1-3 골격)."""
        raise NotImplementedError(
            "build_summary 는 M2 selling 파일럿에서 구현됩니다 "
            "(routes/sales_invoices.py:_build_etax_summary 이관 예정)."
        )
