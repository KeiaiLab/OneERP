"""Order-to-Cash 완전 플로우 E2E — 로그인부터 로그아웃까지.

이 테스트는 다음을 반복 실행 가능하게 보장한다:

  1. 로그인 (Gateway /auth/login) — JWT 획득
  2. 비즈니스 플로우 (고객 → 품목 → 입고 → 수주 → 출고 → 송장 → 수금)
  3. 자동 생성 검증 (분개전표, 매출채권, 잔액 소거)
  4. 로그아웃 (Gateway /auth/logout) — 세션 종료

중복 제거 원칙:
- 각 비즈니스 단계는 `helpers/order_to_cash.py` 함수로 분리
- 로그인/로그아웃은 `otc_auth_session` fixture가 항상 짝을 맞춰 보장
- 검증 단계도 `assert_journal_entry_created`, `assert_ar_outstanding` 헬퍼로 위임
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from tests.e2e.helpers import order_to_cash as otc

if TYPE_CHECKING:
    from tests.e2e.helpers.auth import AuthSession

pytestmark = pytest.mark.e2e


def test_order_to_cash_완전_플로우(
    otc_services: dict[str, str],
    otc_auth_session: AuthSession,
) -> None:
    """로그인 → Order-to-Cash 전체 사이클 → 로그아웃.

    otc_auth_session fixture가 로그인/로그아웃을 자동 짝 처리한다.
    """
    session: AuthSession = otc_auth_session

    # 인증된 서비스 클라이언트 3개 — Bearer 토큰 + 테넌트 헤더 자동 첨부
    with (
        session.client(otc_services["selling"]) as selling,
        session.client(otc_services["stock"]) as stock,
        session.client(otc_services["accounting"]) as accounting,
    ):
        # 1. 기준정보: 고객 + 품목
        customer_id = otc.create_customer(
            selling,
            name="OTC E2E 고객",
            tax_id="111-22-33333",
        )
        item_code = otc.create_item(stock, name="OTC 테스트 제품")

        # 2. 입고로 재고 확보
        otc.receive_stock(
            stock,
            item_code=item_code,
            item_name="OTC 테스트 제품",
            qty=100,
            rate=5000,
            posting_date="2026-03-20",
        )

        # 3. 판매주문
        so_id = otc.create_sales_order(
            selling,
            customer_id=customer_id,
            customer_name="OTC E2E 고객",
            item_code=item_code,
            item_name="OTC 테스트 제품",
            qty=10,
            rate=10000,
            transaction_date="2026-03-20",
            delivery_date="2026-03-25",
        )

        # 4. 납품서
        dn_id = otc.create_delivery_note(
            selling,
            customer_id=customer_id,
            customer_name="OTC E2E 고객",
            sales_order_id=so_id,
            item_code=item_code,
            item_name="OTC 테스트 제품",
            qty=10,
            posting_date="2026-03-22",
        )

        # 5. 매출송장 — 부가세 10% 포함
        invoice = otc.issue_sales_invoice(
            selling,
            customer_id=customer_id,
            customer_name="OTC E2E 고객",
            sales_order_id=so_id,
            delivery_note_id=dn_id,
            item_code=item_code,
            item_name="OTC 테스트 제품",
            qty=10,
            rate=10000,
            tax_rate_pct=10,
            posting_date="2026-03-22",
            due_date="2026-04-22",
        )
        grand_total = invoice["grand_total"]
        assert grand_total == 110000.0, f"예상 합계 110000, 실제 {grand_total}"

        # 6. 이벤트 체인 검증 — 분개전표 자동생성 (selling → accounting)
        otc.assert_journal_entry_created(accounting, voucher_no=invoice["id"])

        # 7. 이벤트 체인 검증 — AR 생성 (outstanding == grand_total)
        otc.assert_ar_outstanding(
            accounting,
            voucher_no=invoice["id"],
            expected_outstanding=grand_total,
        )

        # 8. 수금 제출
        otc.settle_payment(
            accounting,
            customer_id=customer_id,
            customer_name="OTC E2E 고객",
            sales_invoice_id=invoice["id"],
            amount=grand_total,
            posting_date="2026-03-25",
        )

        # 9. AR 잔액 소거 검증 (outstanding == 0)
        otc.assert_ar_outstanding(
            accounting,
            voucher_no=invoice["id"],
            expected_outstanding=0,
        )


def test_login_실패_시_401(otc_services: dict[str, str]) -> None:
    """잘못된 자격증명으로 로그인 시 401이 반환되는지 확인 — 인증 플로우 회귀."""
    import httpx

    resp = httpx.post(
        f"{otc_services['gateway']}/api/v1/auth/login",
        json={"username": "invalid_user", "password": "wrong"},
        headers={"X-Tenant-Id": "default"},
        timeout=10.0,
    )
    assert resp.status_code == 401, (
        f"잘못된 로그인은 401이어야 함 — 실제: {resp.status_code} {resp.text}"
    )


def test_로그아웃_후_재로그인_가능(
    otc_services: dict[str, str],
    seeded_credentials: dict[str, Any],
) -> None:
    """로그아웃 후에도 동일 계정으로 재로그인이 정상 동작해야 함 — 세션 격리 회귀."""
    from tests.e2e.helpers.auth import login, logout

    token1 = login(
        otc_services["gateway"],
        tenant_id=seeded_credentials["tenant_id"],
        username=seeded_credentials["username"],
        password=seeded_credentials["password"],
    )
    logout(
        otc_services["gateway"],
        token=token1,
        tenant_id=seeded_credentials["tenant_id"],
    )
    token2 = login(
        otc_services["gateway"],
        tenant_id=seeded_credentials["tenant_id"],
        username=seeded_credentials["username"],
        password=seeded_credentials["password"],
    )
    assert token1 != "", "첫 번째 토큰이 발급돼야 함"
    assert token2 != "", "두 번째 토큰이 발급돼야 함"
    logout(
        otc_services["gateway"],
        token=token2,
        tenant_id=seeded_credentials["tenant_id"],
    )
