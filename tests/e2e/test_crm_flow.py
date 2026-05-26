"""E2E: FL6 CRM-to-Selling 플로우 — 리드 → 기회 → 파이프라인 → 고객 → 견적 → 판매주문.

CRM(crm) 서비스와 판매(selling) 서비스 간 전체 경로를 검증한다.
"""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


class TestCRMFlow:
    """FL6 CRM-to-Selling 전체 시나리오를 검증한다."""

    def test_리드_워크벤치는_점수와_전환가이드를_반환한다(self, crm_client: httpx.Client) -> None:
        """리드 목록/요약이 점수, 활동, 전환 준비 상태를 보여준다."""
        resp = crm_client.post(
            "/api/v1/leads",
            json={
                "lead_name": "워크벤치 테스트 리드",
                "company_name": "테스트 산업",
                "email": "workbench@test.com",
                "source": "웹세미나",
                "interested_item": "AI CRM",
                "lead_score": 88,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        lead_id = resp.json()["id"]

        resp = crm_client.put(
            f"/api/v1/leads/{lead_id}",
            json={"status": "qualified", "assigned_to": "owner-001"},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = crm_client.post(
            "/api/v1/activities/",
            json={
                "activity_type": "meeting",
                "activity_date": "2026-04-10",
                "party_type": "lead",
                "party": lead_id,
                "description": "데모 미팅",
                "assigned_to": "owner-001",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201

        listing = crm_client.get("/api/v1/leads?status=qualified", headers=HEADERS)
        assert listing.status_code == 200
        listing_data = listing.json()
        assert listing_data["summary"]["qualified_count"] >= 1
        assert listing_data["summary"]["high_score_count"] >= 1
        lead_row = next(item for item in listing_data["data"] if item["_id"] == lead_id)
        assert lead_row["status_badge"] == "qualified_hot"
        assert lead_row["recommended_action"] == "convert_to_opportunity"
        assert lead_row["activity_summary"]["activity_count"] == 1

        summary = crm_client.get(f"/api/v1/leads/{lead_id}/summary", headers=HEADERS)
        assert summary.status_code == 200
        summary_data = summary.json()
        assert summary_data["score_summary"]["lead_score"] == 88.0
        assert summary_data["score_summary"]["score_grade"] == "hot"
        assert summary_data["activity_summary"]["latest_activity_type"] == "meeting"
        assert summary_data["conversion_summary"]["can_convert_to_opportunity"] is True
        assert summary_data["recommended_action"] == "convert_to_opportunity"

    # ------------------------------------------------------------------
    # 1. 리드 CRUD 기본 검증
    # ------------------------------------------------------------------
    def test_리드_CRUD(self, crm_client: httpx.Client) -> None:
        """Lead 생성 → 조회 → 수정 → 삭제."""
        resp = crm_client.post(
            "/api/v1/leads",
            json={
                "lead_name": "E2E 리드 김대표",
                "company_name": "테스트 주식회사",
                "email": "lead@test.com",
                "phone": "010-1234-5678",
                "source": "웹사이트",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        lead_id = resp.json()["id"]

        # 조회
        resp = crm_client.get(f"/api/v1/leads/{lead_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["lead_name"] == "E2E 리드 김대표"

        # 수정
        resp = crm_client.put(
            f"/api/v1/leads/{lead_id}",
            json={
                "status": "contacted",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 목록
        resp = crm_client.get("/api/v1/leads", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 삭제
        resp = crm_client.delete(f"/api/v1/leads/{lead_id}", headers=HEADERS)
        assert resp.status_code == 204

    # ------------------------------------------------------------------
    # 2. 기회 생성 → 제출
    # ------------------------------------------------------------------
    def test_기회_생성_제출(self, crm_client: httpx.Client) -> None:
        """Opportunity 생성 → 제출 워크플로우."""
        # 리드 생성
        resp = crm_client.post(
            "/api/v1/leads",
            json={
                "lead_name": "기회 테스트 리드",
                "company_name": "기회 회사",
            },
            headers=HEADERS,
        )
        lead_id = resp.json()["id"]

        # 기회 생성
        resp = crm_client.post(
            "/api/v1/opportunities",
            json={
                "lead_ref": lead_id,
                "opportunity_type": "sales",
                "expected_amount": 50000000,
                "probability": 0.7,
                "close_date": "2026-06-30",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        opp_id = resp.json()["id"]

        # 조회
        resp = crm_client.get(f"/api/v1/opportunities/{opp_id}", headers=HEADERS)
        assert resp.status_code == 200
        opp = resp.json()
        assert opp["expected_amount"] == 50000000
        assert opp["probability"] == 0.7

        # 제출
        resp = crm_client.post(f"/api/v1/opportunities/{opp_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # 3. 리드→기회 전환(convert) 시나리오
    # ------------------------------------------------------------------
    def test_리드에서_기회_전환_시나리오(self, crm_client: httpx.Client) -> None:
        """리드 생성 → 자격부여 → 기회 생성(리드 참조) 전체 플로우."""
        # 리드 생성
        resp = crm_client.post(
            "/api/v1/leads",
            json={
                "lead_name": "전환 테스트 리드",
                "company_name": "전환 회사",
                "email": "convert@test.com",
            },
            headers=HEADERS,
        )
        lead_id = resp.json()["id"]

        # 리드 → qualified 상태로 변경
        resp = crm_client.put(
            f"/api/v1/leads/{lead_id}",
            json={
                "status": "qualified",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 기회 생성 (리드 참조)
        resp = crm_client.post(
            "/api/v1/opportunities",
            json={
                "lead_ref": lead_id,
                "opportunity_type": "sales",
                "expected_amount": 10000000,
                "probability": 0.5,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        opp_id = resp.json()["id"]

        # 기회에서 리드 참조 확인
        resp = crm_client.get(f"/api/v1/opportunities/{opp_id}", headers=HEADERS)
        assert resp.json()["lead_ref"] == lead_id

    # ------------------------------------------------------------------
    # 4. 리드→기회 자동 전환(convert 엔드포인트) 시나리오
    # ------------------------------------------------------------------
    def test_리드_자동_전환(self, crm_client: httpx.Client) -> None:
        """리드 convert 엔드포인트로 자동 기회 전환."""
        # 리드 생성
        resp = crm_client.post(
            "/api/v1/leads",
            json={
                "lead_name": "자동전환 리드",
                "company_name": "자동전환 회사",
                "email": "auto@test.com",
            },
            headers=HEADERS,
        )
        lead_id = resp.json()["id"]

        # convert 엔드포인트 호출
        resp = crm_client.post(f"/api/v1/leads/{lead_id}/convert", headers=HEADERS)
        assert resp.status_code == 200
        result = resp.json()
        assert result["lead_id"] == lead_id
        assert "opportunity_id" in result

        # 리드 상태가 converted로 변경 확인
        resp = crm_client.get(f"/api/v1/leads/{lead_id}", headers=HEADERS)
        assert resp.json()["status"] == "converted"

    # ------------------------------------------------------------------
    # 5. 기회 파이프라인 단계 진행 (advance-stage)
    # ------------------------------------------------------------------
    def test_기회_파이프라인_단계진행(self, crm_client: httpx.Client) -> None:
        """기회 단계 open → quotation → won 진행."""
        # 리드 + 기회 생성
        resp = crm_client.post(
            "/api/v1/leads",
            json={"lead_name": "파이프라인 테스트", "company_name": "PL 회사"},
            headers=HEADERS,
        )
        lead_id = resp.json()["id"]

        resp = crm_client.post(
            "/api/v1/opportunities",
            json={
                "lead_ref": lead_id,
                "opportunity_type": "sales",
                "expected_amount": 30000000,
                "probability": 0.6,
            },
            headers=HEADERS,
        )
        opp_id = resp.json()["id"]

        # open → quotation 단계 진행
        resp = crm_client.post(
            f"/api/v1/opportunities/{opp_id}/advance-stage",
            json={"stage": "quotation"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["new_stage"] == "quotation"

        # quotation → won 단계 진행
        resp = crm_client.post(
            f"/api/v1/opportunities/{opp_id}/advance-stage",
            json={"stage": "won"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["new_stage"] == "won"

    # ------------------------------------------------------------------
    # 6. 기회 실패(lost) 처리
    # ------------------------------------------------------------------
    def test_기회_실패_처리(self, crm_client: httpx.Client) -> None:
        """기회 lost 처리 + 사유 기록."""
        resp = crm_client.post(
            "/api/v1/leads",
            json={"lead_name": "실패 테스트", "company_name": "실패 회사"},
            headers=HEADERS,
        )
        lead_id = resp.json()["id"]

        resp = crm_client.post(
            "/api/v1/opportunities",
            json={
                "lead_ref": lead_id,
                "opportunity_type": "sales",
                "expected_amount": 5000000,
                "probability": 0.3,
            },
            headers=HEADERS,
        )
        opp_id = resp.json()["id"]

        # 실패 처리
        resp = crm_client.post(
            f"/api/v1/opportunities/{opp_id}/lost",
            json={"lost_reason": "가격 경쟁력 부족", "competitor": "경쟁사 A"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "lost"
        assert result["lost_reason"] == "가격 경쟁력 부족"

    # ------------------------------------------------------------------
    # 7. 기회→견적 전환 (convert-to-quotation) — CRM→Selling 크로스 서비스
    # ------------------------------------------------------------------
    def test_기회에서_견적_전환(self, crm_client: httpx.Client) -> None:
        """기회 convert-to-quotation 호출 (이벤트 기반 비동기 전환)."""
        resp = crm_client.post(
            "/api/v1/leads",
            json={"lead_name": "견적전환 테스트", "company_name": "견적 회사"},
            headers=HEADERS,
        )
        lead_id = resp.json()["id"]

        resp = crm_client.post(
            "/api/v1/opportunities",
            json={
                "lead_ref": lead_id,
                "opportunity_type": "sales",
                "expected_amount": 20000000,
                "probability": 0.8,
            },
            headers=HEADERS,
        )
        opp_id = resp.json()["id"]

        # 견적 전환 요청 — Outbox 이벤트 발행
        resp = crm_client.post(
            f"/api/v1/opportunities/{opp_id}/convert-to-quotation",
            json={
                "customer_id": "CUST-QTN-001",
                "items": [
                    {"item_code": "ITEM-CRM-01", "item_name": "CRM 품목", "qty": 10, "rate": 2000},
                ],
                "valid_till": "2026-06-30",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["opportunity_id"] == opp_id

    # ------------------------------------------------------------------
    # 8. 판매(Selling) 측 견적→판매주문 전체 흐름 (CRM에서 넘어온 후)
    # ------------------------------------------------------------------
    def test_견적_생성_확정_판매주문_전환(self, selling_client: httpx.Client) -> None:
        """견적 생성 → 제출(확정) → 판매주문 생성 → 판매주문 제출."""
        # 고객 생성
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "CRM→판매 테스트 고객",
                "customer_type": "company",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        # 견적 생성
        resp = selling_client.post(
            "/api/v1/quotations",
            json={
                "customer_id": customer_id,
                "customer_name": "CRM→판매 테스트 고객",
                "transaction_date": "2026-03-27",
                "valid_till": "2026-04-27",
                "items": [
                    {"item_code": "ITEM-FL6-A", "item_name": "FL6 품목 A", "qty": 5, "rate": 3000},
                    {"item_code": "ITEM-FL6-B", "item_name": "FL6 품목 B", "qty": 3, "rate": 5000},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        qtn_id = resp.json()["id"]

        # 견적 조회 — 총액 검증
        resp = selling_client.get(f"/api/v1/quotations/{qtn_id}", headers=HEADERS)
        assert resp.status_code == 200
        qtn = resp.json()
        assert qtn["total"] == 30000.0  # 5*3000 + 3*5000
        assert qtn["docstatus"] == 0

        # 견적 제출(확정)
        resp = selling_client.post(f"/api/v1/quotations/{qtn_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        # 견적 확정 상태 확인
        resp = selling_client.get(f"/api/v1/quotations/{qtn_id}", headers=HEADERS)
        assert resp.json()["docstatus"] == 1

        # 판매주문 생성 (견적 참조)
        resp = selling_client.post(
            "/api/v1/sales-orders",
            json={
                "customer_id": customer_id,
                "customer_name": "CRM→판매 테스트 고객",
                "transaction_date": "2026-03-27",
                "delivery_date": "2026-04-10",
                "items": [
                    {"item_code": "ITEM-FL6-A", "item_name": "FL6 품목 A", "qty": 5, "rate": 3000},
                    {"item_code": "ITEM-FL6-B", "item_name": "FL6 품목 B", "qty": 3, "rate": 5000},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        so_id = resp.json()["id"]

        # 판매주문 총액 검증
        resp = selling_client.get(f"/api/v1/sales-orders/{so_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] == 30000.0

        # 판매주문 제출
        resp = selling_client.post(f"/api/v1/sales-orders/{so_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # 9. 기회 성사(won) 표시
    # ------------------------------------------------------------------
    def test_기회_성사_표시(self, crm_client: httpx.Client) -> None:
        """기회 won 엔드포인트를 통한 성사 처리."""
        resp = crm_client.post(
            "/api/v1/leads",
            json={"lead_name": "성사 테스트", "company_name": "성사 회사"},
            headers=HEADERS,
        )
        lead_id = resp.json()["id"]

        resp = crm_client.post(
            "/api/v1/opportunities",
            json={
                "lead_ref": lead_id,
                "opportunity_type": "sales",
                "expected_amount": 15000000,
                "probability": 0.9,
            },
            headers=HEADERS,
        )
        opp_id = resp.json()["id"]

        # won 표시
        resp = crm_client.post(f"/api/v1/opportunities/{opp_id}/won", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["new_stage"] == "won"
