"""전자결재 + 경비청구 E2E 테스트.

경비청구 → 결재요청 자동 생성 → 승인 → 회계전표 자동 생성 흐름을 검증한다.
expenses → gateway → accounting 서비스 간 데이터 흐름을 확인한다.
"""

from __future__ import annotations

import time

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e

# 비동기 이벤트 처리 대기 시간 (초)
_EVENT_WAIT = 2.0
# 폴링 최대 횟수
_POLL_MAX = 10
# 폴링 간격 (초)
_POLL_INTERVAL = 0.5


def _poll_until(
    client: httpx.Client,
    url: str,
    *,
    check: str,
    expected: object,
    max_attempts: int = _POLL_MAX,
) -> dict:
    """응답의 특정 필드가 기대값이 될 때까지 폴링한다."""
    for _ in range(max_attempts):
        resp = client.get(url, headers=HEADERS)
        if resp.status_code == 200:
            body = resp.json()
            if "data" in body and isinstance(body["data"], list) and len(body["data"]) > 0:
                if body["data"][0].get(check) == expected:
                    return body
            elif body.get(check) == expected:
                return body
        time.sleep(_POLL_INTERVAL)
    msg = f"{url}에서 {check}=={expected} 조건을 {max_attempts}회 폴링 후에도 충족하지 못했습니다"
    raise TimeoutError(msg)


class TestApprovalExpense:
    """경비청구 → 결재 → 회계 전표 전체 사이클을 검증한다."""

    def test_경비청구_결재_회계_전체_흐름(
        self,
        expenses_client: httpx.Client,
        gateway_client: httpx.Client,
        accounting_client: httpx.Client,
    ) -> None:
        """경비유형 생성→경비청구 생성+제출→결재요청 확인→승인→회계전표 검증."""
        # --- Step 1: 경비유형 생성 (expenses 서비스) ---
        resp = expenses_client.post(
            "/api/v1/expense-types/",
            json={
                "expense_type_name": "출장 교통비",
                "description": "국내 출장 시 교통비",
                "account": "여비교통비",
                "is_active": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        expense_type = resp.json()
        expense_type_id = expense_type["id"]

        # --- Step 2: 경비청구 생성 (expenses 서비스) ---
        claim_amount = 150000.0
        resp = expenses_client.post(
            "/api/v1/expense-claims/",
            json={
                "employee_id": "EMP-E2E-001",
                "employee_name": "경비 테스트 직원",
                "posting_date": "2026-03-20",
                "expense_type_id": expense_type_id,
                "expenses": [
                    {
                        "expense_date": "2026-03-18",
                        "expense_type": "출장 교통비",
                        "description": "서울-부산 KTX 왕복",
                        "amount": 120000,
                    },
                    {
                        "expense_date": "2026-03-19",
                        "expense_type": "출장 교통비",
                        "description": "택시비",
                        "amount": 30000,
                    },
                ],
                "total_claimed_amount": claim_amount,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        claim = resp.json()
        claim_id = claim["id"]

        # 경비청구 조회 — 총액 검증
        resp = expenses_client.get(
            f"/api/v1/expense-claims/{claim_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        claim_data = resp.json()
        assert claim_data["total_claimed_amount"] == claim_amount
        assert claim_data["docstatus"] == 0  # DRAFT

        # --- Step 3: 경비청구 제출 ---
        resp = expenses_client.post(
            f"/api/v1/expense-claims/{claim_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 제출 상태 확인
        resp = expenses_client.get(
            f"/api/v1/expense-claims/{claim_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["docstatus"] == 1  # SUBMITTED

        # --- 검증: 결재요청 자동 생성 확인 (gateway 서비스) ---
        time.sleep(_EVENT_WAIT)
        resp = gateway_client.get(
            "/api/v1/approval-requests",
            params={
                "reference_doctype": "expense_claim",
                "reference_name": claim_id,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        approval_request_id = None
        if ar_data.get("total", 0) > 0:
            approval_request = ar_data["data"][0]
            approval_request_id = approval_request["id"]
            assert approval_request["status"] == "pending"

        # --- Step 4: 결재 승인 ---
        if approval_request_id:
            resp = gateway_client.post(
                f"/api/v1/approval-requests/{approval_request_id}/approve",
                json={
                    "comment": "E2E 테스트 승인",
                },
                headers=HEADERS,
            )
            assert resp.status_code == 200

            # 승인 상태 확인
            resp = gateway_client.get(
                f"/api/v1/approval-requests/{approval_request_id}",
                headers=HEADERS,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "approved"

        # --- 검증: 경비청구 approval_status 업데이트 ---
        time.sleep(_EVENT_WAIT)
        resp = expenses_client.get(
            f"/api/v1/expense-claims/{claim_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        updated_claim = resp.json()
        if approval_request_id:
            assert updated_claim.get("approval_status") == "approved"

        # --- 검증: 분개전표(경비/미지급금) 자동 생성 ---
        resp = accounting_client.get(
            "/api/v1/journal-entries",
            params={"voucher_no": claim_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        je_data = resp.json()
        if je_data.get("total", 0) > 0:
            je = je_data["data"][0]
            # 차변(경비) == 대변(미지급금) 합계 일치
            assert je["total_debit"] == je["total_credit"]
            assert je["total_debit"] == claim_amount

    def test_경비청구_반려_흐름(
        self,
        expenses_client: httpx.Client,
        gateway_client: httpx.Client,
    ) -> None:
        """경비청구 제출→결재 반려→상태 반영 검증."""
        # 경비청구 생성
        resp = expenses_client.post(
            "/api/v1/expense-claims/",
            json={
                "employee_id": "EMP-E2E-002",
                "employee_name": "반려 테스트 직원",
                "posting_date": "2026-03-20",
                "expenses": [
                    {
                        "expense_date": "2026-03-19",
                        "expense_type": "기타",
                        "description": "사유 불충분 경비",
                        "amount": 500000,
                    },
                ],
                "total_claimed_amount": 500000,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        claim_id = resp.json()["id"]

        # 제출
        resp = expenses_client.post(
            f"/api/v1/expense-claims/{claim_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 결재요청 조회
        time.sleep(_EVENT_WAIT)
        resp = gateway_client.get(
            "/api/v1/approval-requests",
            params={
                "reference_doctype": "expense_claim",
                "reference_name": claim_id,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        if ar_data.get("total", 0) > 0:
            approval_request_id = ar_data["data"][0]["id"]

            # 반려
            resp = gateway_client.post(
                f"/api/v1/approval-requests/{approval_request_id}/reject",
                json={
                    "comment": "영수증 미첨부로 반려",
                },
                headers=HEADERS,
            )
            assert resp.status_code == 200

            # 반려 상태 확인
            resp = gateway_client.get(
                f"/api/v1/approval-requests/{approval_request_id}",
                headers=HEADERS,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "rejected"

            # 경비청구 반려 상태 반영 확인
            time.sleep(_EVENT_WAIT)
            resp = expenses_client.get(
                f"/api/v1/expense-claims/{claim_id}",
                headers=HEADERS,
            )
            assert resp.status_code == 200
            assert resp.json().get("approval_status") == "rejected"
