"""E2E: 회계 플로우 — Account → JournalEntry → CostCenter → ETaxInvoice."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestAccountingFlow:
    """회계 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_계정과목_CRUD(self, accounting_client: httpx.Client) -> None:
        """계정과목 생성 → 조회 → 수정 → 삭제."""
        resp = accounting_client.post(
            "/api/v1/accounts",
            json={
                "account_name": "E2E 자산 계정",
                "account_type": "asset",
                "is_group": False,
                "currency": "KRW",
            },
        )
        assert resp.status_code == 201
        doc_id = resp.json()["_id"]

        # 조회
        resp = accounting_client.get(f"/api/v1/accounts/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["account_type"] == "asset"

        # 수정
        resp = accounting_client.put(
            f"/api/v1/accounts/{doc_id}",
            json={
                "account_name": "E2E 수정 자산 계정",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = accounting_client.delete(f"/api/v1/accounts/{doc_id}")
        assert resp.status_code == 204

    def test_계정과목_계층구조(self, accounting_client: httpx.Client) -> None:
        """부모-자식 계정과목 트리 구조 검증."""
        # 그룹 계정 생성
        resp = accounting_client.post(
            "/api/v1/accounts",
            json={
                "account_name": "유동자산",
                "account_type": "asset",
                "is_group": True,
            },
        )
        parent_id = resp.json()["_id"]

        # 자식 계정 생성
        resp = accounting_client.post(
            "/api/v1/accounts",
            json={
                "account_name": "현금",
                "account_type": "asset",
                "parent_account": parent_id,
            },
        )
        assert resp.status_code == 201
        child_id = resp.json()["_id"]

        # 자식 조회 — parent 확인
        resp = accounting_client.get(f"/api/v1/accounts/{child_id}")
        assert resp.json()["parent_account"] == parent_id

    def test_분개전표_생성_제출_취소(self, accounting_client: httpx.Client) -> None:
        """JournalEntry 생성(차대변 일치) → 제출 → 취소."""
        resp = accounting_client.post(
            "/api/v1/journal-entries",
            json={
                "posting_date": "2026-03-17",
                "voucher_type": "journal_entry",
                "items": [
                    {"account": "현금", "debit": 10000, "credit": 0},
                    {"account": "매출", "debit": 0, "credit": 10000},
                ],
                "remark": "E2E 분개 테스트",
            },
        )
        assert resp.status_code == 201
        je_id = resp.json()["_id"]

        # 조회 — 차대변 합계 검증
        resp = accounting_client.get(f"/api/v1/journal-entries/{je_id}")
        assert resp.status_code == 200
        je = resp.json()
        assert je["total_debit"] == 10000.0
        assert je["total_credit"] == 10000.0
        assert je["docstatus"] == 0

        # 제출
        resp = accounting_client.post(f"/api/v1/journal-entries/{je_id}/submit")
        assert resp.status_code == 200

        # 취소
        resp = accounting_client.post(f"/api/v1/journal-entries/{je_id}/cancel")
        assert resp.status_code == 200

    def test_분개전표_차대변_불일치_거부(self, accounting_client: httpx.Client) -> None:
        """차변 != 대변인 분개전표는 거부되어야 한다."""
        resp = accounting_client.post(
            "/api/v1/journal-entries",
            json={
                "posting_date": "2026-03-17",
                "items": [
                    {"account": "현금", "debit": 10000, "credit": 0},
                    {"account": "매출", "debit": 0, "credit": 5000},
                ],
            },
        )
        assert resp.status_code == 422  # 유효성 검증 실패

    def test_코스트센터_CRUD(self, accounting_client: httpx.Client) -> None:
        """CostCenter 생성 → 조회 → 수정 → 삭제."""
        resp = accounting_client.post(
            "/api/v1/cost-centers",
            json={
                "cost_center_name": "E2E 본사",
                "company": "E2E 회사",
            },
        )
        assert resp.status_code == 201
        cc_id = resp.json()["_id"]

        resp = accounting_client.get(f"/api/v1/cost-centers/{cc_id}")
        assert resp.status_code == 200
        assert resp.json()["cost_center_name"] == "E2E 본사"

        resp = accounting_client.put(
            f"/api/v1/cost-centers/{cc_id}",
            json={
                "cost_center_name": "E2E 수정 본사",
            },
        )
        assert resp.status_code == 200

        resp = accounting_client.delete(f"/api/v1/cost-centers/{cc_id}")
        assert resp.status_code == 204

    def test_전자세금계산서_생성_제출(self, accounting_client: httpx.Client) -> None:
        """ETaxInvoice 생성 → 제출."""
        resp = accounting_client.post(
            "/api/v1/etax-invoices",
            json={
                "invoice_ref": "SINV-2026-00001",
                "issue_date": "2026-03-17",
                "supplier_or_customer": "테스트 고객",
                "supply_amount": 100000,
                "tax_amount": 10000,
            },
        )
        assert resp.status_code == 201
        etax_id = resp.json()["_id"]

        # 조회
        resp = accounting_client.get(f"/api/v1/etax-invoices/{etax_id}")
        assert resp.status_code == 200
        etax = resp.json()
        assert etax["transmission_status"] == "pending"

        # 제출
        resp = accounting_client.post(f"/api/v1/etax-invoices/{etax_id}/submit")
        assert resp.status_code == 200
