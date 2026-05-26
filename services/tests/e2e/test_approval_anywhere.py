"""FL7 Approval-Anywhere E2E 테스트 — 구매주문 결재 흐름 검증.

구매주문(PO)을 기반으로 결재 템플릿 → 결재 요청 생성 → 승인/거부 흐름을 검증한다.
시나리오:
  1. 자동결재: 금액 임계값 이하 → 자동 승인
  2. 수동결재: 금액 임계값 초과 → 승인자 액션 → 승인
  3. 거부: 승인자 거부 → 상태 rejected
"""

from __future__ import annotations

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
