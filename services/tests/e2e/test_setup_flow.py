"""E2E: 설정 플로우 — Company → WorkflowRule → NotificationTemplate."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestSetupFlow:
    """설정 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_회사_CRUD(self, gateway_client: httpx.Client) -> None:
        """Company 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/companies",
            json={
                "company_name": "E2E 주식회사",
                "abbr": "E2E",
                "default_currency": "KRW",
                "country": "KR",
                "fiscal_year_start": "01-01",
            },
        )
        assert resp.status_code == 201
        company_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/companies/{company_id}")
        assert resp.status_code == 200
        assert resp.json()["company_name"] == "E2E 주식회사"

        # 수정
        resp = gateway_client.put(
            f"/api/v1/companies/{company_id}",
            json={
                "domain": "제조업",
            },
        )
        assert resp.status_code == 200

        # 목록
        resp = gateway_client.get("/api/v1/companies")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 삭제
        resp = gateway_client.delete(f"/api/v1/companies/{company_id}")
        assert resp.status_code == 204

    def test_워크플로우_규칙_CRUD(self, gateway_client: httpx.Client) -> None:
        """WorkflowRule 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/workflow-rules",
            json={
                "document_type": "SalesOrder",
                "states": [
                    {"state_name": "초안", "allow_edit": True, "doc_status": 0},
                    {"state_name": "승인", "allow_edit": False, "doc_status": 1},
                ],
                "transitions": [
                    {
                        "from_state": "초안",
                        "to_state": "승인",
                        "allowed_roles": ["manager"],
                    },
                ],
            },
        )
        assert resp.status_code == 201
        wf_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/workflow-rules/{wf_id}")
        assert resp.status_code == 200
        wf = resp.json()
        assert wf["document_type"] == "SalesOrder"
        assert len(wf["states"]) == 2
        assert len(wf["transitions"]) == 1

        # 삭제
        resp = gateway_client.delete(f"/api/v1/workflow-rules/{wf_id}")
        assert resp.status_code == 204

    def test_알림_템플릿_CRUD(self, gateway_client: httpx.Client) -> None:
        """NotificationTemplate 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/notification-templates",
            json={
                "name": "E2E 주문 알림",
                "document_type": "SalesOrder",
                "event": "on_submit",
                "channel": "email",
                "subject_template": "주문 {{doc.name}} 승인",
                "message_template": "주문이 승인되었습니다.",
            },
        )
        assert resp.status_code == 201
        nt_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/notification-templates/{nt_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "E2E 주문 알림"

        # 수정
        resp = gateway_client.put(
            f"/api/v1/notification-templates/{nt_id}",
            json={
                "channel": "system",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = gateway_client.delete(f"/api/v1/notification-templates/{nt_id}")
        assert resp.status_code == 204
