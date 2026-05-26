"""E2E: 회계 플로우 — Account → JournalEntry → CostCenter → ETaxInvoice."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from tests.e2e.conftest import wait_for_condition
from tests.e2e.helpers.api_client import HEADERS, doc_id

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
        account_id = doc_id(resp.json())

        # 조회
        resp = accounting_client.get(f"/api/v1/accounts/{account_id}")
        assert resp.status_code == 200
        assert resp.json()["account_type"] == "asset"

        # 수정
        resp = accounting_client.put(
            f"/api/v1/accounts/{account_id}",
            json={
                "account_name": "E2E 수정 자산 계정",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = accounting_client.delete(f"/api/v1/accounts/{account_id}")
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
        parent_id = doc_id(resp.json())

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
        child_id = doc_id(resp.json())

        # 자식 조회 — parent 확인
        resp = accounting_client.get(f"/api/v1/accounts/{child_id}")
        assert resp.json()["parent_account"] == parent_id

    def test_예산_워크벤치는_집행률과_버전_이전_요약을_반환한다(
        self,
        accounting_client: httpx.Client,
    ) -> None:
        """예산 목록/상세는 집행 경고와 버전·이전 현황을 함께 보여줘야 한다."""
        primary_resp = accounting_client.post(
            "/api/v1/budgets",
            json={
                "budget_name": "영업본부 2026 예산",
                "fiscal_year": "FY-2026",
                "cost_center": "CC-SALES-E2E",
                "budget_amount": 1000000,
                "actual_amount": 950000,
                "items": [
                    {"account": "ACC-100", "budget_amount": 600000, "actual_amount": 620000},
                    {"account": "ACC-200", "budget_amount": 400000, "actual_amount": 330000},
                ],
            },
            headers=HEADERS,
        )
        assert primary_resp.status_code == 201
        primary_id = primary_resp.json()["_id"]

        reserve_resp = accounting_client.post(
            "/api/v1/budgets",
            json={
                "budget_name": "예비비 2026 예산",
                "fiscal_year": "FY-2026",
                "cost_center": "CC-RESERVE-E2E",
                "budget_amount": 500000,
                "actual_amount": 50000,
                "items": [{"account": "ACC-300", "budget_amount": 500000, "actual_amount": 50000}],
            },
            headers=HEADERS,
        )
        assert reserve_resp.status_code == 201
        reserve_id = reserve_resp.json()["_id"]

        version_resp = accounting_client.post(
            "/api/v1/budget-versions",
            json={
                "budget_id": primary_id,
                "version_no": 2,
                "version_name": "Q2 조정안",
                "total_amount": 1000000,
                "is_current": True,
            },
            headers=HEADERS,
        )
        assert version_resp.status_code == 201

        transfer_resp = accounting_client.post(
            "/api/v1/budget-transfers",
            json={
                "from_budget_id": primary_id,
                "to_budget_id": reserve_id,
                "transfer_amount": 150000,
                "transfer_date": "2026-04-01",
                "reason": "예비비 재배정",
            },
            headers=HEADERS,
        )
        assert transfer_resp.status_code == 201

        submit_resp = accounting_client.post(
            f"/api/v1/budgets/{primary_id}/submit", headers=HEADERS
        )
        assert submit_resp.status_code == 200

        listing_resp = accounting_client.get(
            "/api/v1/budgets?status_badge=near_limit&page=1&page_size=20",
            headers=HEADERS,
        )
        assert listing_resp.status_code == 200
        listing = listing_resp.json()
        assert listing["total"] == 1
        assert listing["summary"]["near_limit_count"] == 1
        assert listing["summary"]["pending_transfer_count"] == 1
        assert listing["data"][0]["_id"] == primary_id
        assert listing["data"][0]["status_badge"] == "near_limit"
        assert listing["data"][0]["recommended_action"] == "review_budget_transfer"

        detail_resp = accounting_client.get(f"/api/v1/budgets/{primary_id}", headers=HEADERS)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["budget_usage_summary"]["utilization_rate"] == 95.0
        assert detail["budget_usage_summary"]["over_budget_item_count"] == 1
        assert detail["version_summary"]["version_count"] == 1
        assert detail["version_summary"]["current_version_name"] == "Q2 조정안"
        assert detail["transfer_summary"]["pending_transfer_count"] == 1
        assert detail["available_actions"] == [
            "cancel",
            "open_budget_versions",
            "open_budget_transfers",
            "create_budget_transfer",
        ]

    def test_회계기간_워크벤치는_마감검증과_재개가이드를_반환한다(
        self,
        accounting_client: httpx.Client,
    ) -> None:
        """회계기간 목록/상세/마감/재개가 운영자 워크벤치 계약을 충족해야 한다."""
        today = datetime.now(tz=UTC).date()
        first_day = today.replace(day=1)
        past_end = first_day - timedelta(days=1)
        past_start = past_end.replace(day=1)

        fiscal_year_resp = accounting_client.post(
            "/api/v1/fiscal-years",
            json={
                "year_name": str(today.year),
                "start_date": f"{today.year}-01-01",
                "end_date": f"{today.year}-12-31",
                "company": "원ERP 주식회사",
            },
            headers=HEADERS,
        )
        assert fiscal_year_resp.status_code == 201
        fiscal_year_id = fiscal_year_resp.json()["_id"]

        ready_resp = accounting_client.post(
            "/api/v1/accounting-periods",
            json={
                "period_name": f"{past_start:%Y-%m}",
                "start_date": past_start.isoformat(),
                "end_date": past_end.isoformat(),
                "company": "원ERP 주식회사",
                "status": "open",
                "fiscal_year": fiscal_year_id,
            },
            headers=HEADERS,
        )
        assert ready_resp.status_code == 201
        ready_id = ready_resp.json()["id"]

        listing_resp = accounting_client.get(
            "/api/v1/accounting-periods?status_badge=close_ready&page=1&page_size=20",
            headers=HEADERS,
        )
        assert listing_resp.status_code == 200
        listing = listing_resp.json()
        assert listing["total"] == 1
        assert listing["summary"]["close_ready_count"] == 1
        assert listing["summary"]["total_draft_entries"] == 0
        assert listing["data"][0]["_id"] == ready_id
        assert listing["data"][0]["status_badge"] == "close_ready"
        assert listing["data"][0]["recommended_action"] == "close_period"

        summary_resp = accounting_client.get(
            f"/api/v1/accounting-periods/{ready_id}/summary",
            headers=HEADERS,
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["close_validation_summary"]["closeable"] is True
        assert summary["available_actions"] == [
            "edit",
            "open_journal_entries",
            "validate_close",
            "close",
        ]

        close_resp = accounting_client.post(
            f"/api/v1/accounting-periods/{ready_id}/close",
            json={"closing_account": "ACC-RETAINED", "remarks": "E2E 월마감"},
            headers=HEADERS,
        )
        assert close_resp.status_code == 200
        closed = close_resp.json()
        assert closed["status_badge"] == "closed_reopenable"
        assert closed["close_result"]["status"] == "closed"
        assert closed["close_result"]["pcv_id"].startswith("PCV-")

        reopen_resp = accounting_client.post(
            f"/api/v1/accounting-periods/{ready_id}/reopen",
            headers=HEADERS,
        )
        assert reopen_resp.status_code == 200
        reopened = reopen_resp.json()
        assert reopened["status"] == "open"
        assert reopened["status_badge"] == "close_ready"

    def test_부가세신고_워크벤치는_세액집계와_전자세금계산서_연계를_반환한다(
        self,
        accounting_client: httpx.Client,
    ) -> None:
        """부가세 신고는 분기별 세액 집계와 전자세금계산서 동기화 현황을 함께 보여줘야 한다."""
        for posting_date, items in (
            (
                "2026-01-12",
                [
                    {"account": "현금", "debit": 330000, "credit": 0},
                    {"account": "매출", "debit": 0, "credit": 300000},
                    {"account": "부가세예수금", "debit": 0, "credit": 30000},
                ],
            ),
            (
                "2026-02-03",
                [
                    {"account": "비용", "debit": 120000, "credit": 0},
                    {"account": "부가세대급금", "debit": 12000, "credit": 0},
                    {"account": "미지급금", "debit": 0, "credit": 132000},
                ],
            ),
            (
                "2026-03-20",
                [
                    {"account": "예금", "debit": 220000, "credit": 0},
                    {"account": "매출", "debit": 0, "credit": 200000},
                    {"account": "부가세예수금", "debit": 0, "credit": 20000},
                ],
            ),
        ):
            resp = accounting_client.post(
                "/api/v1/journal-entries",
                json={
                    "posting_date": posting_date,
                    "voucher_type": "tax_adjustment",
                    "items": items,
                    "remark": f"VAT E2E {posting_date}",
                },
                headers=HEADERS,
            )
            assert resp.status_code == 201
            journal_id = resp.json()["_id"]
            submit_resp = accounting_client.post(
                f"/api/v1/journal-entries/{journal_id}/submit",
                headers=HEADERS,
            )
            assert submit_resp.status_code == 200

        for transmission_status in ("pending", "transmitted"):
            resp = accounting_client.post(
                "/api/v1/etax-invoices",
                json={
                    "invoice_ref": f"ETAX-{transmission_status}",
                    "issue_date": "2026-03-25",
                    "supplier_or_customer": "VAT 고객",
                    "supply_amount": 1000000,
                    "tax_amount": 100000,
                    "transmission_status": transmission_status,
                },
                headers=HEADERS,
            )
            assert resp.status_code == 201

        create_resp = accounting_client.post(
            "/api/v1/vat-returns",
            json={"period": "2026-Q1"},
            headers=HEADERS,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        vat_return_id = created["id"]
        assert created["tax_summary"] == {
            "output_tax": 50000.0,
            "input_tax": 12000.0,
            "net_tax": 38000.0,
            "payable_tax": 38000.0,
            "refundable_tax": 0.0,
        }
        assert created["invoice_sync_summary"] == {
            "issued_count": 2,
            "transmitted_count": 1,
            "pending_count": 1,
            "failed_count": 0,
        }

        submit_resp = accounting_client.post(
            f"/api/v1/vat-returns/{vat_return_id}/submit",
            headers=HEADERS,
        )
        assert submit_resp.status_code == 200
        submitted = submit_resp.json()
        assert submitted["status_badge"] == "submitted_payable"

        listing_resp = accounting_client.get(
            "/api/v1/vat-returns?status_badge=submitted_payable&page=1&page_size=20",
            headers=HEADERS,
        )
        assert listing_resp.status_code == 200
        listing = listing_resp.json()
        assert listing["total"] == 1
        assert listing["summary"] == {
            "draft_count": 0,
            "submitted_count": 1,
            "cancelled_count": 0,
            "payable_count": 1,
            "refund_count": 0,
            "overdue_count": 0,
        }
        assert listing["data"][0]["_id"] == vat_return_id
        assert listing["data"][0]["recommended_action"] == "schedule_tax_payment"

        summary_resp = accounting_client.get(
            f"/api/v1/vat-returns/{vat_return_id}/summary",
            headers=HEADERS,
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["period_scope_summary"] == {
            "period": "2026-Q1",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "filing_cycle": "quarterly",
            "due_date": "2026-04-25",
        }
        assert summary["tax_summary"]["payable_tax"] == 38000.0
        assert summary["invoice_sync_summary"]["pending_count"] == 1
        assert summary["available_actions"] == [
            "view_filing_history",
            "open_etax_invoices",
            "schedule_tax_payment",
            "cancel",
        ]

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
            headers=HEADERS,
        )
        assert resp.status_code == 201
        je_id = resp.json()["_id"]

        # 조회 — 차대변 합계 검증
        resp = accounting_client.get(f"/api/v1/journal-entries/{je_id}", headers=HEADERS)
        assert resp.status_code == 200
        je = resp.json()
        assert je["total_debit"] == 10000.0
        assert je["total_credit"] == 10000.0
        assert je["docstatus"] == 0

        # 제출
        resp = accounting_client.post(f"/api/v1/journal-entries/{je_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        # 취소
        resp = accounting_client.post(f"/api/v1/journal-entries/{je_id}/cancel", headers=HEADERS)
        assert resp.status_code == 200

    def test_분개전표_초안_삭제_및_제출후_삭제거부(self, accounting_client: httpx.Client) -> None:
        """초안 전표는 삭제할 수 있고, 제출 후에는 삭제가 거부되어야 한다."""
        draft_resp = accounting_client.post(
            "/api/v1/journal-entries",
            json={
                "posting_date": "2026-03-18",
                "voucher_type": "journal_entry",
                "items": [
                    {"account": "현금", "debit": 5000, "credit": 0},
                    {"account": "매출", "debit": 0, "credit": 5000},
                ],
                "remark": "삭제 가능한 초안 분개",
            },
            headers=HEADERS,
        )
        assert draft_resp.status_code == 201
        draft_id = draft_resp.json()["_id"]

        delete_resp = accounting_client.delete(
            f"/api/v1/journal-entries/{draft_id}",
            headers=HEADERS,
        )
        assert delete_resp.status_code == 204

        not_found_resp = accounting_client.get(
            f"/api/v1/journal-entries/{draft_id}",
            headers=HEADERS,
        )
        assert not_found_resp.status_code == 404

        submitted_resp = accounting_client.post(
            "/api/v1/journal-entries",
            json={
                "posting_date": "2026-03-18",
                "voucher_type": "journal_entry",
                "items": [
                    {"account": "현금", "debit": 7000, "credit": 0},
                    {"account": "매출", "debit": 0, "credit": 7000},
                ],
                "remark": "삭제 불가 제출 분개",
            },
            headers=HEADERS,
        )
        assert submitted_resp.status_code == 201
        submitted_id = submitted_resp.json()["_id"]

        submit_resp = accounting_client.post(
            f"/api/v1/journal-entries/{submitted_id}/submit",
            headers=HEADERS,
        )
        assert submit_resp.status_code == 200

        blocked_resp = accounting_client.delete(
            f"/api/v1/journal-entries/{submitted_id}",
            headers=HEADERS,
        )
        assert blocked_resp.status_code == 400

    def test_분개전표_승인워크플로우_및_반복전표_템플릿(
        self, accounting_client: httpx.Client
    ) -> None:
        """반복 전표 템플릿 생성 → 초안 생성 → 승인 요청 → 승인 제출."""
        template_resp = accounting_client.post(
            "/api/v1/journal-entries/templates",
            json={
                "template_name": "월말 선급비용",
                "voucher_type": "recurring_adjustment",
                "recurrence_unit": "monthly",
                "interval": 1,
                "next_posting_date": "2026-04-30",
                "items": [
                    {"account": "선급비용", "debit": 500000, "credit": 0},
                    {"account": "보험료", "debit": 0, "credit": 500000},
                ],
                "remark": "월말 선급비용 조정",
                "default_approver": "finance-lead",
            },
            headers=HEADERS,
        )
        assert template_resp.status_code == 201
        template_id = template_resp.json()["_id"]

        instantiate_resp = accounting_client.post(
            f"/api/v1/journal-entries/templates/{template_id}/instantiate",
            json={"posting_date": "2026-04-30"},
            headers=HEADERS,
        )
        assert instantiate_resp.status_code == 201
        draft_id = instantiate_resp.json()["_id"]
        assert instantiate_resp.json()["required_approver"] == "finance-lead"

        request_resp = accounting_client.post(
            f"/api/v1/journal-entries/{draft_id}/request-approval",
            json={"approver": "finance-lead", "comment": "월말 조정 승인 요청"},
            headers=HEADERS,
        )
        assert request_resp.status_code == 200
        assert request_resp.json()["approval_status"] == "pending"

        approve_resp = accounting_client.post(
            f"/api/v1/journal-entries/{draft_id}/approve",
            headers={**HEADERS, "X-User-Sub": "finance-lead"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["approval_status"] == "approved"

        je_resp = accounting_client.get(f"/api/v1/journal-entries/{draft_id}", headers=HEADERS)
        assert je_resp.status_code == 200
        entry = je_resp.json()
        assert entry["docstatus"] == 1
        assert entry["approval_status"] == "approved"

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
            headers=HEADERS,
        )
        assert resp.status_code == 422  # 유효성 검증 실패

    def test_매출채권_상세는_고객별_독촉추적과_후속액션을_보여준다(
        self,
        selling_client: httpx.Client,
        accounting_client: httpx.Client,
    ) -> None:
        """판매송장 제출 후 매출채권 상세에서 고객별 미수금 요약과 독촉 맥락을 확인한다."""
        customer_resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "AR E2E 고객",
                "customer_type": "company",
            },
            headers=HEADERS,
        )
        assert customer_resp.status_code == 201
        customer_id = customer_resp.json()["_id"]

        invoice_resp = selling_client.post(
            "/api/v1/sales-invoices",
            json={
                "customer_id": customer_id,
                "customer_name": "AR E2E 고객",
                "posting_date": "2026-02-01",
                "due_date": "2026-03-01",
                "items": [
                    {"item_code": "ITEM-AR", "item_name": "AR 품목", "qty": 3, "rate": 50000},
                ],
                "taxes": [
                    {"tax_type": "부가세", "rate": 10, "amount": 15000},
                ],
            },
            headers=HEADERS,
        )
        assert invoice_resp.status_code == 201
        invoice_id = invoice_resp.json()["id"]

        submit_resp = selling_client.post(
            f"/api/v1/sales-invoices/{invoice_id}/submit",
            headers=HEADERS,
        )
        assert submit_resp.status_code == 200

        def _ar_ready():
            resp = accounting_client.get(
                "/api/v1/accounts-receivable",
                params={"voucher_no": invoice_id, "as_of_date": "2026-04-20"},
                headers=HEADERS,
            )
            if resp.status_code != 200:
                return None
            payload = resp.json()
            if payload.get("total", 0) <= 0:
                return None
            return payload

        ar_payload = wait_for_condition(
            _ar_ready,
            timeout=10.0,
            interval=0.5,
            description="매출채권 생성 대기",
        )
        receivable = ar_payload["data"][0]
        receivable_id = receivable["_id"]

        dunning_resp = accounting_client.post(
            "/api/v1/dunnings",
            json={
                "customer": receivable["customer"],
                "outstanding_amount": receivable["outstanding_amount"],
                "dunning_level": 2,
                "dunning_date": "2026-04-05",
                "dunning_fee": 3300,
            },
            headers=HEADERS,
        )
        assert dunning_resp.status_code == 201
        dunning_id = dunning_resp.json()["_id"]

        dunning_submit_resp = accounting_client.post(
            f"/api/v1/dunnings/{dunning_id}/submit",
            headers=HEADERS,
        )
        assert dunning_submit_resp.status_code == 200

        list_resp = accounting_client.get(
            "/api/v1/accounts-receivable",
            params={
                "customer": receivable["customer"],
                "voucher_no": invoice_id,
                "overdue_only": "true",
                "min_overdue_days": 30,
                "as_of_date": "2026-04-20",
            },
            headers=HEADERS,
        )
        assert list_resp.status_code == 200
        list_payload = list_resp.json()
        assert list_payload["summary"]["customer_count"] == 1
        assert list_payload["summary"]["priority_customer_count"] == 1
        customer_summary = list_payload["summary"]["customer_breakdown"][0]
        assert customer_summary["customer"] == receivable["customer"]
        assert customer_summary["latest_dunning_level"] == 2
        assert customer_summary["collection_status"] == "critical_dunning"
        assert customer_summary["recommended_action"] == "call_customer"

        detail_resp = accounting_client.get(
            f"/api/v1/accounts-receivable/{receivable_id}",
            params={"as_of_date": "2026-04-20"},
            headers=HEADERS,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["_id"] == receivable_id
        assert detail["collection_status"] == "critical_dunning"
        assert detail["recommended_action"] == "call_customer"
        assert detail["available_actions"] == [
            "open_invoice",
            "register_payment",
            "view_dunning_history",
        ]
        assert detail["dunning_summary"]["latest_dunning_level"] == 2
        assert detail["dunning_summary"]["latest_dunning_id"] == dunning_id
        assert detail["customer_summary"]["outstanding_amount"] == receivable["outstanding_amount"]
        assert detail["customer_summary"]["overdue_invoice_count"] == 1

    def test_총계정원장_조회_드릴다운과_다축필터(self, accounting_client: httpx.Client) -> None:
        """분개 제출 후 총계정원장에서 계정/기간/원천유형/원가센터 드릴다운이 가능해야 한다."""
        resp = accounting_client.post(
            "/api/v1/journal-entries",
            json={
                "posting_date": "2026-03-21",
                "voucher_type": "sales_invoice",
                "items": [
                    {
                        "account": "현금",
                        "debit": 15000,
                        "credit": 0,
                        "cost_center": "CC-E2E-001",
                    },
                    {
                        "account": "매출",
                        "debit": 0,
                        "credit": 15000,
                        "cost_center": "CC-E2E-001",
                    },
                ],
                "remark": "총계정원장 E2E",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        je_id = resp.json()["_id"]

        resp = accounting_client.post(f"/api/v1/journal-entries/{je_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = accounting_client.get(
            "/api/v1/general-ledger-entries",
            params={
                "account": "현금",
                "posting_date_from": "2026-03-21",
                "posting_date_to": "2026-03-21",
                "voucher_type": "sales_invoice",
                "cost_center": "CC-E2E-001",
                "page": 1,
                "page_size": 10,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ledger = resp.json()
        assert ledger["total"] == 1
        assert ledger["summary"]["total_debit"] == 15000.0
        assert ledger["summary"]["total_credit"] == 0.0
        entry = ledger["data"][0]
        assert entry["journal_entry_id"] == je_id
        assert entry["account"] == "현금"
        assert entry["debit"] == 15000.0
        assert entry["voucher_type"] == "sales_invoice"
        assert entry["cost_center"] == "CC-E2E-001"
        assert entry["running_balance"] == 15000.0

        resp = accounting_client.get(
            f"/api/v1/general-ledger-entries/{entry['entry_id']}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["journal_entry_id"] == je_id
        assert detail["voucher_type"] == "sales_invoice"
        assert detail["remarks"] == "총계정원장 E2E"

    def test_원가센터_트리와_삭제제약(self, accounting_client: httpx.Client) -> None:
        """원가센터 생성 → 트리 조회 → 분개 참조 후 삭제 차단."""
        resp = accounting_client.post(
            "/api/v1/cost-centers",
            json={
                "cost_center_name": "E2E 본사",
                "company": "E2E 회사",
                "is_group": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        parent_id = resp.json()["_id"]

        resp = accounting_client.post(
            "/api/v1/cost-centers",
            json={
                "cost_center_name": "E2E 영업부",
                "company": "E2E 회사",
                "parent_cost_center": parent_id,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        child_id = resp.json()["_id"]

        tree_resp = accounting_client.get("/api/v1/cost-centers/tree", headers=HEADERS)
        assert tree_resp.status_code == 200
        tree_payload = tree_resp.json()
        assert tree_payload["summary"]["group_count"] >= 1
        assert tree_payload["summary"]["company_counts"]["E2E 회사"] >= 2
        root = next(node for node in tree_payload["data"] if node["_id"] == parent_id)
        assert root["children"][0]["_id"] == child_id

        resp = accounting_client.post(
            "/api/v1/journal-entries",
            json={
                "posting_date": "2026-03-22",
                "voucher_type": "journal_entry",
                "items": [
                    {
                        "account": "현금",
                        "debit": 20000,
                        "credit": 0,
                        "cost_center": child_id,
                    },
                    {
                        "account": "매출",
                        "debit": 0,
                        "credit": 20000,
                        "cost_center": child_id,
                    },
                ],
                "remark": "원가센터 E2E",
            },
        )
        assert resp.status_code == 201
        journal_entry_id = resp.json()["_id"]

        resp = accounting_client.post(
            f"/api/v1/journal-entries/{journal_entry_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        blocked_by_child = accounting_client.delete(
            f"/api/v1/cost-centers/{parent_id}",
            headers=HEADERS,
        )
        assert blocked_by_child.status_code == 422
        assert blocked_by_child.json()["error"] == "ERR-ACCT-031"

        blocked_by_usage = accounting_client.delete(
            f"/api/v1/cost-centers/{child_id}",
            headers=HEADERS,
        )
        assert blocked_by_usage.status_code == 422
        assert blocked_by_usage.json()["error"] == "ERR-ACCT-032"

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
        etax_id = doc_id(resp.json())

        # 조회
        resp = accounting_client.get(f"/api/v1/etax-invoices/{etax_id}")
        assert resp.status_code == 200
        etax = resp.json()
        assert etax["transmission_status"] == "pending"

        # 제출
        resp = accounting_client.post(f"/api/v1/etax-invoices/{etax_id}/submit")
        assert resp.status_code == 200
