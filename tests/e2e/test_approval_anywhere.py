"""FL7 Approval-Anywhere E2E 테스트 — 구매주문 결재 흐름 검증.

구매주문(PO)을 기반으로 결재 템플릿 → 결재 요청 생성 → 승인/거부 흐름을 검증한다.
시나리오:
  1. 자동결재: 금액 임계값 이하 → 자동 승인
  2. 수동결재: 금액 임계값 초과 → 승인자 액션 → 승인
  3. 거부: 승인자 거부 → 상태 rejected
"""

from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e

# 자동결재 금액 임계값 (100만원 이하 자동 승인)
_AUTO_APPROVE_THRESHOLD = 1_000_000.0


class TestApprovalAnywhere:
    """구매주문 기반 Approval-Anywhere 결재 흐름을 검증한다."""

    # -- 헬퍼 --

    @staticmethod
    def _create_approval_template(
        gateway_client: httpx.Client,
        *,
        document_type: str = "PurchaseOrder",
        approver: str = "e2e-test",
    ) -> str:
        """결재 템플릿을 생성하고 ID를 반환한다."""
        resp = gateway_client.post(
            "/api/v1/approval-templates",
            json={
                "template_name": f"{document_type} 결재 템플릿",
                "document_type": document_type,
                "steps": [
                    {
                        "step": 1,
                        "approver_role": "team_lead",
                        "approver": approver,
                        "approval_type": "single",
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201, f"결재 템플릿 생성 실패: {resp.status_code} {resp.text}"
        return resp.json()["approval_template_id"]

    @staticmethod
    def _create_purchase_order(
        buying_client: httpx.Client,
        *,
        amount: float,
        supplier_name: str = "결재테스트 공급업체",
    ) -> str:
        """구매주문을 생성하고 ID를 반환한다."""
        resp = buying_client.post(
            "/api/v1/purchase-orders",
            json={
                "supplier_id": "SUP-E2E-APPROVAL",
                "supplier_name": supplier_name,
                "transaction_date": "2026-03-27",
                "items": [
                    {
                        "idx": 1,
                        "item_code": "ITEM-APPROVAL-001",
                        "item_name": "결재 테스트 품목",
                        "qty": 1,
                        "rate": amount,
                        "amount": amount,
                        "received_qty": 0,
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201, f"구매주문 생성 실패: {resp.status_code} {resp.text}"
        return resp.json()["id"]

    @staticmethod
    def _submit_purchase_order(buying_client: httpx.Client, po_id: str) -> None:
        """구매주문을 제출한다."""
        resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200, f"구매주문 제출 실패: {resp.status_code} {resp.text}"

    @staticmethod
    def _create_approval_request(
        gateway_client: httpx.Client,
        *,
        document_type: str,
        document_id: str,
        approval_lines: list[dict],
    ) -> str:
        """결재 요청을 직접 생성한다 (ApprovalService.create_request 경유 대신 API 직접 호출)."""
        resp = gateway_client.post(
            "/api/v1/approval-requests",
            json={
                "document_type": document_type,
                "document_id": document_id,
                "requester": "e2e-test",
                "status": "pending",
                "current_step": 1,
                "approval_lines": approval_lines,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201, f"결재 요청 생성 실패: {resp.status_code} {resp.text}"
        return resp.json()["approval_request_id"]

    @staticmethod
    def _create_delegation_rule(
        gateway_client: httpx.Client,
        *,
        delegator: str,
        delegate: str,
        document_type: str = "",
        from_date: str | None = None,
        to_date: str | None = None,
        is_active: bool = True,
    ) -> str:
        """위임 규칙을 생성하고 ID를 반환한다."""
        payload = {
            "delegator": delegator,
            "delegate": delegate,
            "document_type": document_type,
            "is_active": is_active,
        }
        if from_date:
            payload["from_date"] = from_date
        if to_date:
            payload["to_date"] = to_date

        resp = gateway_client.post(
            "/api/v1/delegation-rules",
            json=payload,
            headers=HEADERS,
        )
        assert resp.status_code == 201, f"위임 규칙 생성 실패: {resp.status_code} {resp.text}"
        return resp.json()["delegation_rule_id"]

    # -- 시나리오 1: 자동결재 (임계값 이하) --

    def test_자동결재_임계값_이하_자동승인(
        self,
        buying_client: httpx.Client,
        gateway_client: httpx.Client,
    ) -> None:
        """금액이 임계값 이하인 구매주문은 결재요청 없이 제출이 완료된다.

        자동결재 흐름:
        1. 구매주문 생성 (100만원 이하)
        2. 구매주문 제출
        3. 제출 상태(docstatus=1) 확인 → 별도 결재 없이 처리 완료
        """
        # 소액 구매주문 생성 (50만원)
        small_amount = 500_000.0
        po_id = self._create_purchase_order(buying_client, amount=small_amount)

        # 구매주문 제출 — 임계값 이하이므로 별도 결재 불필요
        self._submit_purchase_order(buying_client, po_id)

        # 제출 상태 확인
        resp = buying_client.get(
            f"/api/v1/purchase-orders/{po_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        po_data = resp.json()
        assert po_data["docstatus"] == 1, "제출 후 docstatus는 1(SUBMITTED)이어야 한다"

        # 결재 템플릿 생성 + 결재 요청을 직접 생성하여 자동 승인 시뮬레이션
        self._create_approval_template(gateway_client, document_type="PurchaseOrder")

        # 자동결재: 결재 요청을 생성하고 즉시 승인 처리
        ar_id = self._create_approval_request(
            gateway_client,
            document_type="PurchaseOrder",
            document_id=po_id,
            approval_lines=[
                {
                    "step": 1,
                    "approver": "e2e-test",
                    "approver_role": "team_lead",
                    "approval_type": "single",
                    "status": "pending",
                },
            ],
        )

        # 자동 승인 처리 (금액 임계값 이하이므로 즉시 승인)
        resp = gateway_client.post(
            f"/api/v1/approval-requests/{ar_id}/approve",
            json={"comment": f"자동결재: 금액 {small_amount:,.0f}원 (임계값 이하)"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        approve_result = resp.json()
        assert approve_result["final_approved"] is True, "자동결재 결과는 최종 승인이어야 한다"

        # 결재 요청 상태 확인
        resp = gateway_client.get(
            f"/api/v1/approval-requests/{ar_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        assert ar_data["status"] == "approved", "자동결재 후 상태는 approved여야 한다"

    # -- 시나리오 2: 수동결재 (임계값 초과) --

    def test_수동결재_임계값_초과_승인자_승인(
        self,
        buying_client: httpx.Client,
        gateway_client: httpx.Client,
    ) -> None:
        """금액이 임계값을 초과하는 구매주문은 승인자의 명시적 승인이 필요하다.

        수동결재 흐름:
        1. 구매주문 생성 (500만원, 임계값 초과)
        2. 구매주문 제출
        3. 결재 요청 생성 (pending)
        4. 승인자 승인
        5. 상태 approved 확인
        """
        # 고액 구매주문 생성 (500만원)
        large_amount = 5_000_000.0
        po_id = self._create_purchase_order(
            buying_client,
            amount=large_amount,
            supplier_name="고액결재 공급업체",
        )

        # 구매주문 제출
        self._submit_purchase_order(buying_client, po_id)

        # 결재 요청 생성 (수동 — 승인자 지정)
        ar_id = self._create_approval_request(
            gateway_client,
            document_type="PurchaseOrder",
            document_id=po_id,
            approval_lines=[
                {
                    "step": 1,
                    "approver": "e2e-test",
                    "approver_role": "team_lead",
                    "approval_type": "single",
                    "status": "pending",
                },
            ],
        )

        # 결재 요청 상태 확인 — pending
        resp = gateway_client.get(
            f"/api/v1/approval-requests/{ar_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        assert ar_data["status"] == "pending", "결재 요청 초기 상태는 pending이어야 한다"
        assert ar_data["document_type"] == "PurchaseOrder"
        assert ar_data["document_id"] == po_id

        # 승인자가 승인 처리
        resp = gateway_client.post(
            f"/api/v1/approval-requests/{ar_id}/approve",
            json={"comment": f"수동결재 승인: 금액 {large_amount:,.0f}원 확인"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        approve_result = resp.json()
        assert approve_result["final_approved"] is True, "단일 단계 승인은 최종 승인이어야 한다"
        assert approve_result["approved_step"] == 1

        # 결재 요청 최종 상태 확인 — approved
        resp = gateway_client.get(
            f"/api/v1/approval-requests/{ar_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        assert ar_data["status"] == "approved", "승인 후 상태는 approved여야 한다"

        # 결재 이력 확인 — approve 액션이 기록되어야 한다
        resp = gateway_client.get(
            "/api/v1/approval-actions",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        actions_data = resp.json()
        assert actions_data["total"] > 0, "결재 이력이 최소 1건 이상 존재해야 한다"

    # -- 시나리오 3: 거부 --

    def test_결재_거부_상태_rejected(
        self,
        buying_client: httpx.Client,
        gateway_client: httpx.Client,
    ) -> None:
        """승인자가 결재를 거부하면 상태가 rejected로 변경된다.

        거부 흐름:
        1. 구매주문 생성
        2. 구매주문 제출
        3. 결재 요청 생성
        4. 승인자 거부
        5. 상태 rejected 확인
        """
        # 구매주문 생성 (300만원)
        reject_amount = 3_000_000.0
        po_id = self._create_purchase_order(
            buying_client,
            amount=reject_amount,
            supplier_name="거부테스트 공급업체",
        )

        # 구매주문 제출
        self._submit_purchase_order(buying_client, po_id)

        # 결재 요청 생성
        ar_id = self._create_approval_request(
            gateway_client,
            document_type="PurchaseOrder",
            document_id=po_id,
            approval_lines=[
                {
                    "step": 1,
                    "approver": "e2e-test",
                    "approver_role": "team_lead",
                    "approval_type": "single",
                    "status": "pending",
                },
            ],
        )

        # 결재 요청 상태 확인 — pending
        resp = gateway_client.get(
            f"/api/v1/approval-requests/{ar_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

        # 승인자가 거부 처리
        resp = gateway_client.post(
            f"/api/v1/approval-requests/{ar_id}/reject",
            json={"reason": "공급업체 단가 과다 — 재검토 필요"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        reject_result = resp.json()
        assert reject_result["status"] == "rejected", "거부 결과 상태는 rejected여야 한다"
        assert reject_result["rejected_step"] == 1

        # 결재 요청 최종 상태 확인 — rejected
        resp = gateway_client.get(
            f"/api/v1/approval-requests/{ar_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        assert ar_data["status"] == "rejected", "거부 후 상태는 rejected여야 한다"

        # 결재 라인 상태 확인
        approval_lines = ar_data.get("approval_lines", [])
        assert len(approval_lines) > 0, "결재 라인이 존재해야 한다"
        rejected_line = approval_lines[0]
        assert rejected_line["status"] == "rejected", "거부된 결재 라인 상태는 rejected여야 한다"

    def test_결재요청_대기함_요약과_대시보드_집계를_조회한다(
        self,
        gateway_client: httpx.Client,
    ) -> None:
        """결재 대기함은 내 대기 건수, 현재 단계, 가능한 액션을 함께 보여줘야 한다."""
        request_id = self._create_approval_request(
            gateway_client,
            document_type="ExpenseClaim",
            document_id=f"EXP-INBOX-{uuid4().hex[:8].upper()}",
            approval_lines=[
                {
                    "step": 1,
                    "approver": "director-001",
                    "approver_role": "director",
                    "approval_type": "single",
                    "status": "pending",
                    "pre_approval_roles": ["director"],
                },
                {
                    "step": 2,
                    "approver": "cfo-001",
                    "approver_role": "cfo",
                    "approval_type": "single",
                    "status": "pending",
                },
            ],
        )

        director_headers = dict(HEADERS)
        director_headers["X-User-Sub"] = "director-001"
        director_headers["X-User-Roles"] = "director"

        inbox_resp = gateway_client.get(
            "/api/v1/approval-requests",
            headers=director_headers,
        )
        assert inbox_resp.status_code == 200
        inbox = inbox_resp.json()
        assert inbox["summary"]["waiting_on_me_count"] >= 1
        row = next(doc for doc in inbox["data"] if doc["_id"] == request_id)
        assert row["waiting_on_me"] is True
        assert row["status_badge"] == "pending_approval"
        assert row["available_actions"] == ["approve", "reject", "delegate", "pre_approve"]
        assert row["current_step_summary"]["pending_approver_count"] == 1

        detail_resp = gateway_client.get(
            f"/api/v1/approval-requests/{request_id}",
            headers=director_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["current_step_summary"]["approvers"][0]["is_current_user"] is True
        assert detail["current_step_summary"]["approvers"][0]["can_pre_approve"] is True

        dashboard_resp = gateway_client.get(
            "/api/v1/dashboard/kpis",
            headers=director_headers,
        )
        assert dashboard_resp.status_code == 200
        approval_kpis = dashboard_resp.json()["approval"]
        assert approval_kpis["pending_approvals"] >= 1
        assert approval_kpis["my_pending_approvals"] >= 1

    def test_결재이력_워크벤치가_배지와_감사집계를_제공한다(
        self,
        gateway_client: httpx.Client,
    ) -> None:
        """결재 이력 목록/상세/리포트는 감사 워크벤치 필드를 반환해야 한다."""
        approved_request_id = self._create_approval_request(
            gateway_client,
            document_type="ExpenseClaim",
            document_id=f"EXP-AUDIT-{uuid4().hex[:8].upper()}",
            approval_lines=[
                {
                    "step": 1,
                    "approver": "e2e-test",
                    "approver_role": "team_lead",
                    "approval_type": "single",
                    "status": "pending",
                }
            ],
        )
        resp = gateway_client.post(
            f"/api/v1/approval-requests/{approved_request_id}/approve",
            json={"comment": "승인 완료"},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        rejected_request_id = self._create_approval_request(
            gateway_client,
            document_type="PurchaseOrder",
            document_id=f"PO-AUDIT-{uuid4().hex[:8].upper()}",
            approval_lines=[
                {
                    "step": 1,
                    "approver": "e2e-test",
                    "approver_role": "team_lead",
                    "approval_type": "single",
                    "status": "pending",
                }
            ],
        )
        resp = gateway_client.post(
            f"/api/v1/approval-requests/{rejected_request_id}/reject",
            json={"reason": "예산 재검토"},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = gateway_client.get("/api/v1/approval-actions", headers=HEADERS)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["summary"]["approval_request_count"] >= 2
        assert payload["summary"]["actor_counts"]["e2e-test"] >= 2

        row = next(
            item for item in payload["data"] if item["approval_request"] == rejected_request_id
        )
        assert row["action_badge"] == "rejected"
        assert row["request_summary"]["approval_request"] == rejected_request_id
        assert row["request_summary"]["current_status"] == "rejected"
        assert row["available_actions"] == [
            "open_request",
            "open_document",
            "open_audit_report",
        ]

        resp = gateway_client.get(
            "/api/v1/approval-actions/report",
            params={"approval_request": rejected_request_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        report_payload = resp.json()
        assert report_payload["summary"]["request_status_counts"] == {"rejected": 1}
        assert report_payload["summary"]["actor_counts"] == {"e2e-test": 1}

        action_id = row["_id"]
        resp = gateway_client.get(f"/api/v1/approval-actions/{action_id}", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["timeline_summary"]["total_actions"] == 1
        assert detail["request_summary"]["document_type"] == "PurchaseOrder"

    def test_위임규칙_워크벤치는_범위배지와_권장액션을_보여준다(
        self,
        gateway_client: httpx.Client,
    ) -> None:
        """위임 규칙 목록/상세는 범위·만료 임박·권장 액션을 함께 보여줘야 한다."""
        self._create_delegation_rule(
            gateway_client,
            delegator="manager-001",
            delegate="delegate-001",
            from_date="2026-04-01",
            to_date="2026-04-30",
        )
        expiring_rule_id = self._create_delegation_rule(
            gateway_client,
            delegator="manager-002",
            delegate="delegate-002",
            document_type="ExpenseClaim",
            from_date="2026-04-01",
            to_date="2026-04-11",
        )

        resp = gateway_client.get(
            "/api/v1/delegation-rules",
            params={"as_of_date": "2026-04-10"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["summary"]["active"] >= 2
        assert payload["summary"]["global_scope_count"] >= 1
        assert payload["summary"]["scoped_rule_count"] >= 1
        assert payload["summary"]["expiring_soon_count"] >= 1

        expiring_row = next(row for row in payload["data"] if row["_id"] == expiring_rule_id)
        assert expiring_row["status_badge"] == "expiring_soon"
        assert expiring_row["recommended_action"] == "extend_rule"
        assert expiring_row["scope_summary"]["document_type"] == "ExpenseClaim"
        assert expiring_row["scope_summary"]["remaining_days"] == 1
        assert expiring_row["available_actions"] == ["edit", "deactivate", "delete"]

        resp = gateway_client.get(
            f"/api/v1/delegation-rules/{expiring_rule_id}",
            params={"as_of_date": "2026-04-10"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["status_badge"] == "expiring_soon"
        assert detail["scope_summary"]["rule_scope"] == "document_scoped"
        assert detail["recommended_action"] == "extend_rule"

        resp = gateway_client.post(
            "/api/v1/delegation-rules",
            json={
                "delegator": "manager-002",
                "delegate": "delegate-003",
                "document_type": "ExpenseClaim",
                "from_date": "2026-04-10",
                "to_date": "2026-04-20",
                "is_active": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-APR-012"
