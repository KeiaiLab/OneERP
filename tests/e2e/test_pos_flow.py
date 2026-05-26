"""E2E: POS 플로우 — POSProfile → POSTransaction."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import doc_id

pytestmark = pytest.mark.e2e


class TestPOSFlow:
    """POS 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_POS_프로파일_CRUD(self, selling_client: httpx.Client) -> None:
        """POS 프로파일 생성 → 조회 → 수정 → 삭제."""
        # 생성
        resp = selling_client.post(
            "/api/v1/pos-profiles",
            json={
                "name": "E2E 매장 POS",
                "warehouse": "메인 창고",
                "price_list": "표준 판매가",
                "write_off_account": "잡손실",
                "payments": [
                    {"mode_of_payment": "현금", "default": True},
                    {"mode_of_payment": "카드", "default": False},
                ],
            },
        )
        assert resp.status_code == 201
        pos_id = doc_id(resp.json())

        # 조회
        resp = selling_client.get(f"/api/v1/pos-profiles/{pos_id}")
        assert resp.status_code == 200
        profile = resp.json()
        assert profile["name"] == "E2E 매장 POS"
        assert len(profile["payments"]) == 2

        # 수정
        resp = selling_client.put(
            f"/api/v1/pos-profiles/{pos_id}",
            json={
                "name": "E2E 수정 매장",
            },
        )
        assert resp.status_code == 200

        # 목록
        resp = selling_client.get("/api/v1/pos-profiles")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 삭제
        resp = selling_client.delete(f"/api/v1/pos-profiles/{pos_id}")
        assert resp.status_code == 204

    def test_POS_거래_생성_제출(self, selling_client: httpx.Client) -> None:
        """POS 거래 생성 → 제출 워크플로우."""
        # POS 프로파일 생성
        resp = selling_client.post(
            "/api/v1/pos-profiles",
            json={
                "name": "거래 테스트 POS",
                "warehouse": "매장",
                "payments": [{"mode_of_payment": "현금", "default": True}],
            },
        )
        pos_profile_id = doc_id(resp.json())

        # POS 거래 생성
        resp = selling_client.post(
            "/api/v1/pos-transactions",
            json={
                "customer_id": "",
                "customer_name": "현장 고객",
                "pos_profile_ref": pos_profile_id,
                "posting_date": "2026-03-17",
                "items": [
                    {"item_code": "ITEM-POS-1", "item_name": "POS 품목", "qty": 2, "rate": 15000},
                ],
                "payments": [
                    {"mode_of_payment": "현금", "amount": 30000},
                ],
            },
        )
        assert resp.status_code == 201
        txn_id = doc_id(resp.json())

        # 조회
        resp = selling_client.get(f"/api/v1/pos-transactions/{txn_id}")
        assert resp.status_code == 200
        txn = resp.json()
        assert txn["total"] == 30000.0
        assert txn["docstatus"] == 0

        # 제출
        resp = selling_client.post(f"/api/v1/pos-transactions/{txn_id}/submit")
        assert resp.status_code == 200

        # 제출 확인
        resp = selling_client.get(f"/api/v1/pos-transactions/{txn_id}")
        assert resp.json()["docstatus"] == 1
