"""E2E: 설정 플로우 — Company → WorkflowRule → NotificationTemplate."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


class TestSetupFlow:
    """설정 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_사용자_워크벤치는_OIDC_상태와_초대가이드를_반환한다(
        self, gateway_client: httpx.Client
    ) -> None:
        """사용자 생성 → 초대/OIDC 상태 확인 → 비활성화 후 삭제."""
        company_resp = gateway_client.post(
            "/api/v1/companies",
            json={
                "company_name": "OIDC 테스트 법인",
                "abbr": "OIDC",
                "company_code": "OIDC-HQ",
                "default_currency": "KRW",
                "country": "KR",
                "fiscal_year_start": "01-01",
            },
            headers=HEADERS,
        )
        assert company_resp.status_code == 201
        company_id = company_resp.json()["id"]

        user_resp = gateway_client.post(
            "/api/v1/users",
            json={
                "username": "oidc-user",
                "email": "oidc.user@oneerp.io",
                "full_name": "OIDC 사용자",
                "roles": ["finance_manager"],
                "company_id": company_id,
                "department_name": "재무팀",
                "auth_provider": "oidc",
            },
            headers=HEADERS,
        )
        assert user_resp.status_code == 201
        user_id = user_resp.json()["id"]

        resp = gateway_client.get("/api/v1/users", headers=HEADERS)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 1
        assert payload["summary"] == {
            "total_user_count": 1,
            "active_user_count": 1,
            "inactive_user_count": 0,
            "invited_user_count": 1,
            "oidc_linked_count": 0,
            "admin_user_count": 0,
        }
        assert payload["data"][0]["status_badge"] == "oidc_pending"
        assert payload["data"][0]["recommended_action"] == "complete_oidc_link"

        resp = gateway_client.get(f"/api/v1/users/{user_id}/summary", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["access_summary"]["company_id"] == company_id
        assert detail["access_summary"]["department_name"] == "재무팀"
        assert detail["auth_summary"] == {
            "auth_provider": "oidc",
            "oidc_subject": "",
            "invitation_status": "pending",
            "last_login": None,
        }
        assert "resend_invitation" in detail["available_actions"]

        resp = gateway_client.delete(f"/api/v1/users/{user_id}", headers=HEADERS)
        assert resp.status_code == 422
        assert resp.json()["detail"] == "활성 사용자는 삭제할 수 없습니다. 먼저 비활성화하세요"

        resp = gateway_client.put(
            f"/api/v1/users/{user_id}",
            json={"is_active": False},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = gateway_client.delete(f"/api/v1/users/{user_id}", headers=HEADERS)
        assert resp.status_code == 204

        resp = gateway_client.delete(f"/api/v1/companies/{company_id}", headers=HEADERS)
        assert resp.status_code == 204

    def test_회사_CRUD(self, gateway_client: httpx.Client) -> None:
        """Company 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/companies",
            json={
                "company_name": "E2E 주식회사",
                "abbr": "E2E",
                "company_code": "E2E-HQ",
                "business_registration_number": "123-45-67890",
                "representative_name": "홍대표",
                "address": "서울시 강남구 테헤란로 1",
                "default_currency": "KRW",
                "country": "KR",
                "fiscal_year_start": "01-01",
                "is_default": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        company_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/companies/{company_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["company_name"] == "E2E 주식회사"
        assert resp.json()["status_badge"] == "default_company"
        assert resp.json()["hierarchy_summary"]["is_default"] is True

        # 수정
        resp = gateway_client.put(
            f"/api/v1/companies/{company_id}",
            json={
                "domain": "제조업",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 목록
        resp = gateway_client.get("/api/v1/companies", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
        assert resp.json()["summary"]["default_company_count"] == 1

        # 삭제
        resp = gateway_client.delete(f"/api/v1/companies/{company_id}", headers=HEADERS)
        assert resp.status_code == 204

    def test_회사_워크벤치는_요약과_기본회사_삭제제약을_제공한다(
        self, gateway_client: httpx.Client
    ) -> None:
        """회사 워크벤치는 기본/지사 상태와 기본 회사 삭제 제약을 제공해야 한다."""
        default_resp = gateway_client.post(
            "/api/v1/companies",
            json={
                "company_name": "E2E 플랫폼 본사",
                "abbr": "E2P",
                "company_code": "E2E-PLT",
                "business_registration_number": "321-54-98765",
                "representative_name": "박대표",
                "address": "서울시 중구 세종대로 1",
                "default_currency": "KRW",
                "country": "KR",
                "fiscal_year_start": "01-01",
                "is_default": True,
            },
            headers=HEADERS,
        )
        assert default_resp.status_code == 201
        default_company_id = default_resp.json()["id"]

        sibling_resp = gateway_client.post(
            "/api/v1/companies",
            json={
                "company_name": "E2E 미국법인",
                "abbr": "E2U",
                "company_code": "E2E-USA",
                "default_currency": "USD",
                "country": "US",
                "fiscal_year_start": "01-01",
            },
            headers=HEADERS,
        )
        assert sibling_resp.status_code == 201
        sibling_company_id = sibling_resp.json()["id"]

        resp = gateway_client.get("/api/v1/companies", headers=HEADERS)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 2
        assert payload["summary"] == {
            "total_company_count": 2,
            "active_company_count": 2,
            "inactive_company_count": 0,
            "default_company_count": 1,
            "root_company_count": 2,
            "branch_company_count": 0,
        }
        assert payload["data"][0]["status_badge"] == "default_company"
        assert payload["data"][0]["recommended_action"] == "create_branch_company"

        resp = gateway_client.get(f"/api/v1/companies/{default_company_id}", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["status_badge"] == "default_company"
        assert detail["hierarchy_summary"]["child_company_count"] == 0
        assert "create_branch_company" in detail["available_actions"]

        resp = gateway_client.delete(f"/api/v1/companies/{default_company_id}", headers=HEADERS)
        assert resp.status_code == 422
        assert (
            resp.json()["detail"]
            == "기본 회사는 다른 회사를 기본값으로 전환한 뒤 삭제할 수 있습니다"
        )

        resp = gateway_client.post(
            f"/api/v1/companies/{sibling_company_id}/set-default",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = gateway_client.delete(f"/api/v1/companies/{default_company_id}", headers=HEADERS)
        assert resp.status_code == 204

        resp = gateway_client.delete(f"/api/v1/companies/{sibling_company_id}", headers=HEADERS)
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

    def test_결재양식_프리셋_생성_복제와_삭제제약(self, gateway_client: httpx.Client) -> None:
        """결재 양식 프리셋 생성/복제 후 참조 중 삭제 제약을 검증한다."""
        resp = gateway_client.get("/api/v1/approval-templates/presets", headers=HEADERS)
        assert resp.status_code == 200
        preset_codes = {preset["preset_code"] for preset in resp.json()["data"]}
        assert {"general-proposal", "expense-claim", "purchase-request"} <= preset_codes

        resp = gateway_client.post(
            "/api/v1/approval-templates/presets/purchase-request",
            json={"template_name": "E2E 구매요청 표준"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        template_id = resp.json()["approval_template_id"]

        resp = gateway_client.get(f"/api/v1/approval-templates/{template_id}", headers=HEADERS)
        assert resp.status_code == 200
        template = resp.json()
        assert template["template_code"] == "purchase-request"
        assert template["form_fields"][0]["field_key"] == "request_reason"
        assert template["data_binding_fields"][0]["target_field"] == "요청자"

        resp = gateway_client.post(
            f"/api/v1/approval-templates/{template_id}/clone",
            json={"template_name": "E2E 구매요청 표준 복사본"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        clone_id = resp.json()["approval_template_id"]

        resp = gateway_client.get(f"/api/v1/approval-templates/{clone_id}", headers=HEADERS)
        assert resp.status_code == 200
        clone = resp.json()
        assert clone["template_name"] == "E2E 구매요청 표준 복사본"
        assert clone["steps"][0]["approver_role"] == "team_lead"

        resp = gateway_client.post(
            "/api/v1/approval-lines",
            json={
                "template": template_id,
                "sequence": 1,
                "approver_role": "team_lead",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        approval_line_id = resp.json()["approval_line_id"]

        resp = gateway_client.delete(f"/api/v1/approval-templates/{template_id}", headers=HEADERS)
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-APR-008"

        resp = gateway_client.delete(f"/api/v1/approval-lines/{approval_line_id}", headers=HEADERS)
        assert resp.status_code == 200
        resp = gateway_client.delete(f"/api/v1/approval-templates/{clone_id}", headers=HEADERS)
        assert resp.status_code == 200
        resp = gateway_client.delete(f"/api/v1/approval-templates/{template_id}", headers=HEADERS)
        assert resp.status_code == 200

    def test_결재양식_중복_필드정의_거부(self, gateway_client: httpx.Client) -> None:
        """중복 필드/중복 바인딩 대상은 템플릿 생성 시 거부된다."""
        duplicate_field_resp = gateway_client.post(
            "/api/v1/approval-templates",
            json={
                "template_name": "E2E 중복 필드",
                "document_type": "ExpenseClaim",
                "steps": [
                    {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
                ],
                "form_fields": [
                    {"field_key": "expense_amount", "label": "금액"},
                    {"field_key": "expense_amount", "label": "총 금액"},
                ],
            },
            headers=HEADERS,
        )
        assert duplicate_field_resp.status_code == 422
        assert duplicate_field_resp.json()["error"] == "ERR-APR-006"

        duplicate_binding_resp = gateway_client.post(
            "/api/v1/approval-templates",
            json={
                "template_name": "E2E 중복 바인딩",
                "document_type": "ExpenseClaim",
                "steps": [
                    {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
                ],
                "data_binding_fields": [
                    {"target_field": "총금액", "source_field": "total_amount"},
                    {"target_field": "총금액", "source_field": "approved_amount"},
                ],
            },
            headers=HEADERS,
        )
        assert duplicate_binding_resp.status_code == 422
        assert duplicate_binding_resp.json()["error"] == "ERR-APR-007"

    def test_결재선_워크벤치는_합의단계와_전결단계를_요약한다(
        self,
        gateway_client: httpx.Client,
    ) -> None:
        """관리자는 결재선 마스터 목록/상세에서 합의 단계와 전결 가능 단계를 바로 파악해야 한다."""
        resp = gateway_client.post(
            "/api/v1/approval-templates",
            json={
                "template_name": "E2E 결재선 워크벤치",
                "document_type": "PurchaseOrder",
                "steps": [
                    {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        template_id = resp.json()["approval_template_id"]

        first_line_resp = gateway_client.post(
            "/api/v1/approval-lines",
            json={
                "template": template_id,
                "sequence": 1,
                "approver": "team-lead-001",
                "approver_role": "team_lead",
                "approval_type": "consensus",
                "condition": "amount >= 1000000",
            },
            headers=HEADERS,
        )
        assert first_line_resp.status_code == 201

        second_line_resp = gateway_client.post(
            "/api/v1/approval-lines",
            json={
                "template": template_id,
                "sequence": 1,
                "approver": "legal-001",
                "approver_role": "legal_manager",
                "approval_type": "consensus",
                "condition": "amount >= 1000000",
            },
            headers=HEADERS,
        )
        assert second_line_resp.status_code == 201
        second_line_id = second_line_resp.json()["approval_line_id"]

        third_line_resp = gateway_client.post(
            "/api/v1/approval-lines",
            json={
                "template": template_id,
                "sequence": 2,
                "approver": "director-001",
                "approver_role": "director",
                "approval_type": "single",
                "pre_approval_roles": ["director"],
            },
            headers=HEADERS,
        )
        assert third_line_resp.status_code == 201

        list_resp = gateway_client.get(
            f"/api/v1/approval-lines?template={template_id}",
            headers=HEADERS,
        )
        assert list_resp.status_code == 200
        list_payload = list_resp.json()
        assert list_payload["summary"] == {
            "template_count": 1,
            "step_count": 2,
            "consensus_step_count": 1,
            "pre_approval_step_count": 1,
            "conditional_step_count": 1,
        }
        assert list_payload["data"][0]["approval_mode_badge"] == "consensus"
        assert list_payload["data"][0]["step_summary"]["approver_count"] == 2

        detail_resp = gateway_client.get(
            f"/api/v1/approval-lines/{second_line_id}",
            headers=HEADERS,
        )
        assert detail_resp.status_code == 200
        detail_payload = detail_resp.json()
        assert detail_payload["step_summary"] == {
            "template": template_id,
            "sequence": 1,
            "approver_count": 2,
            "approval_mode": "consensus",
            "pre_approval_enabled": False,
            "condition": "amount >= 1000000",
        }
        assert detail_payload["available_actions"] == ["edit", "reorder", "delete"]

        duplicate_resp = gateway_client.post(
            "/api/v1/approval-lines",
            json={
                "template": template_id,
                "sequence": 1,
                "approver": "team-lead-001",
                "approver_role": "team_lead",
                "approval_type": "consensus",
            },
            headers=HEADERS,
        )
        assert duplicate_resp.status_code == 422
        assert duplicate_resp.json()["error"] == "ERR-APR-010"
