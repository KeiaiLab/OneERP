"""E2E: 문서 관리 플로우 — 생성 → 수정 → 제출 → 승인 → 배포 → 공유 → 서명."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


class TestDocumentFlow:
    """문서 관리 사용자 시나리오를 검증한다."""

    def test_보존정책_워크벤치는_연결분류와_폐기대응가이드를_반환한다(
        self,
        gateway_client: httpx.Client,
        documents_client: httpx.Client,
    ) -> None:
        """보존 정책 생성 → 분류 연결 → 워크벤치/삭제 가드 확인."""
        create_resp = gateway_client.post(
            "/api/v1/retention-policies",
            json={
                "policy_name": "세무 서류 5년",
                "description": "세무 문서 법정 보관",
                "retention_years": 5,
                "retention_months": 0,
                "action_on_expiry": "review",
                "requires_approval": True,
                "legal_basis": "국세기본법 제85조의3",
            },
            headers=HEADERS,
        )
        assert create_resp.status_code == 201
        policy_id = create_resp.json()["id"]

        category_resp = documents_client.post(
            "/api/v1/document-categories",
            json={
                "name": "세무 문서",
                "code": "TAX",
                "default_retention_policy": policy_id,
                "default_security_level": "internal",
            },
            headers=HEADERS,
        )
        assert category_resp.status_code == 201

        list_resp = gateway_client.get("/api/v1/retention-policies", headers=HEADERS)
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        assert list_body["total"] == 1
        assert list_body["summary"] == {
            "total_policy_count": 1,
            "active_policy_count": 1,
            "inactive_policy_count": 0,
            "system_policy_count": 0,
            "approval_required_count": 1,
            "mapped_category_count": 1,
            "expiring_document_count": 0,
        }
        row = list_body["data"][0]
        assert row["status_badge"] == "mapped_active"
        assert row["recommended_action"] == "monitor_retention_schedule"
        assert row["scope_summary"]["linked_category_count"] == 1

        summary_resp = gateway_client.get(
            f"/api/v1/retention-policies/{policy_id}/summary",
            headers=HEADERS,
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["category_summary"]["linked_category_names"] == ["세무 문서"]
        assert summary["document_summary"]["active_document_count"] == 0
        assert summary["compliance_summary"] == {
            "action_on_expiry": "review",
            "requires_approval": True,
            "legal_basis": "국세기본법 제85조의3",
            "is_system": False,
        }

        delete_resp = gateway_client.delete(
            f"/api/v1/retention-policies/{policy_id}",
            headers=HEADERS,
        )
        assert delete_resp.status_code == 422
        assert (
            delete_resp.json()["detail"]
            == "연결된 문서 분류 또는 문서가 있는 보존 정책은 삭제할 수 없습니다"
        )

    def test_문서_워크벤치는_생명주기_공유_서명_요약을_반환한다(
        self,
        documents_client: httpx.Client,
    ) -> None:
        retention_resp = documents_client.post(
            "/api/v1/retention-policies",
            json={
                "policy_name": "일반 문서 3년",
                "retention_years": 3,
                "retention_months": 0,
                "auto_dispose": False,
            },
            headers=HEADERS,
        )
        assert retention_resp.status_code == 201
        retention_id = retention_resp.json()["_id"]

        category_resp = documents_client.post(
            "/api/v1/document-categories",
            json={
                "name": "영업 운영",
                "code": "SALES",
                "default_retention_policy": retention_id,
                "default_security_level": "internal",
            },
            headers=HEADERS,
        )
        assert category_resp.status_code == 201
        category_id = category_resp.json()["_id"]

        template_resp = documents_client.post(
            "/api/v1/document-templates",
            json={
                "template_name": "주간 보고서",
                "content_template": "<p>{{department}} {{author_name}} 보고</p>",
                "document_type": "report",
            },
            headers=HEADERS,
        )
        assert template_resp.status_code == 201
        template_id = template_resp.json()["_id"]

        create_resp = documents_client.post(
            "/api/v1/documents",
            json={
                "title": "2026년 2분기 영업 운영 문서",
                "category": category_id,
                "template_id": template_id,
                "template_variables": {
                    "department": "영업팀",
                    "author_name": "김철수",
                },
                "summary": "문서관리 E2E",
                "tags": ["영업", "운영"],
                "author": "EMP-001",
                "department": "DEPT-SALES",
            },
            headers=HEADERS,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        document_id = created["id"]
        assert created["version"] == 1
        assert created["status"] == "draft"

        update_resp = documents_client.put(
            f"/api/v1/documents/{document_id}",
            json={
                "content": "<p>최신 실적 및 운영 지침</p>",
                "change_summary": "실적 수치 반영",
            },
            headers=HEADERS,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["version"] == 2

        submit_resp = documents_client.post(
            f"/api/v1/documents/{document_id}/submit",
            headers=HEADERS,
        )
        assert submit_resp.status_code == 200
        approve_resp = documents_client.post(
            f"/api/v1/documents/{document_id}/approve",
            headers=HEADERS,
        )
        assert approve_resp.status_code == 200
        publish_resp = documents_client.post(
            f"/api/v1/documents/{document_id}/publish",
            headers=HEADERS,
        )
        assert publish_resp.status_code == 200
        assert publish_resp.json()["status"] == "published"

        share_resp = documents_client.post(
            f"/api/v1/documents/{document_id}/share",
            json={
                "share_type": "external_link",
                "permission": "viewer",
                "expires_at": "2026-05-15T00:00:00+00:00",
                "password": "SecureLink123!",
                "max_downloads": 10,
            },
            headers=HEADERS,
        )
        assert share_resp.status_code == 201

        sign_resp = documents_client.post(
            f"/api/v1/documents/{document_id}/sign",
            json={
                "signature_type": "joint_certificate",
                "signature_data": "base64-signature",
                "certificate_info": {"issuer": "한국정보인증"},
            },
            headers=HEADERS,
        )
        assert sign_resp.status_code == 201

        list_resp = documents_client.get(
            "/api/v1/documents",
            params={"q": "영업 운영", "status": "published"},
            headers=HEADERS,
        )
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        assert list_body["total"] == 1
        assert list_body["summary"]["published_count"] == 1
        assert list_body["summary"]["signed_count"] == 1
        assert list_body["summary"]["shared_externally_count"] == 1
        row = list_body["data"][0]
        assert row["status_badge"] == "published_signed"
        assert row["recommended_action"] == "review_external_shares"

        summary_resp = documents_client.get(
            f"/api/v1/documents/{document_id}/summary",
            headers=HEADERS,
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["lifecycle_summary"]["status"] == "published"
        assert summary["version_summary"]["current_version"] == 3
        assert summary["sharing_summary"]["external_link_count"] == 1
        assert summary["signature_summary"]["valid_signature_count"] == 1
        assert summary["audit_summary"]["event_count"] >= 5
