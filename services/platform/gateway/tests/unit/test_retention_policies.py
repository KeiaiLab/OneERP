"""보존 정책(RetentionPolicy) 워크벤치 라우트 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.retention_policies import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)
client_no_raise = TestClient(_app, raise_server_exceptions=False)

TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.retention_policies._get_repo")
@patch("oneerp_gateway_app.routes.retention_policies.generate_name", return_value="RETP-2026-00001")
def test_보존정책_생성은_법규필드와_만료전략을_저장한다(
    mock_name: MagicMock, mock_repo: MagicMock
) -> None:
    """정책 생성 시 보존 기간·만료 처리·법적 근거를 함께 저장해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/retention-policies",
        json={
            "policy_name": "세무 서류 5년",
            "description": "국세기본법 장부 보존",
            "retention_years": 5,
            "retention_months": 0,
            "action_on_expiry": "review",
            "requires_approval": True,
            "legal_basis": "국세기본법 제85조의3",
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["retention_policy_id"] == "RETP-2026-00001"
    assert payload["id"] == "RETP-2026-00001"

    inserted = repo.insert.call_args.args[0]
    assert inserted.policy_name == "세무 서류 5년"
    assert inserted.description == "국세기본법 장부 보존"
    assert inserted.retention_years == 5
    assert inserted.retention_months == 0
    assert inserted.action_on_expiry == "review"
    assert inserted.requires_approval is True
    assert inserted.legal_basis == "국세기본법 제85조의3"
    assert inserted.is_system is False
    mock_name.assert_called_once_with("RETP", tenant_id="test-tenant")


@patch("oneerp_gateway_app.routes.retention_policies._get_document_repo")
@patch("oneerp_gateway_app.routes.retention_policies._get_category_repo")
@patch("oneerp_gateway_app.routes.retention_policies._get_repo")
def test_보존정책_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_repo: MagicMock,
    mock_category_repo: MagicMock,
    mock_document_repo: MagicMock,
) -> None:
    """정책 목록은 연결 분류/만료 임박 문서/폐기 승인 여부를 한 번에 보여줘야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "RETP-001",
            "policy_name": "세무 서류 5년",
            "retention_years": 5,
            "retention_months": 0,
            "action_on_expiry": "review",
            "requires_approval": True,
            "legal_basis": "국세기본법 제85조의3",
            "is_system": True,
            "is_active": True,
        },
        {
            "_id": "RETP-002",
            "policy_name": "휴면 정책",
            "retention_years": 3,
            "retention_months": 0,
            "action_on_expiry": "archive",
            "requires_approval": False,
            "legal_basis": "",
            "is_system": False,
            "is_active": False,
        },
    ]
    mock_repo.return_value = repo

    category_repo = MagicMock()
    category_repo.find_many.side_effect = lambda query, **kwargs: (
        [{"_id": "DC-001", "name": "세무 문서", "default_retention_policy": "RETP-001"}]
        if query.get("default_retention_policy") == "RETP-001"
        else []
    )
    mock_category_repo.return_value = category_repo

    document_repo = MagicMock()
    document_repo.find_many.side_effect = lambda query, **kwargs: (
        [
            {
                "_id": "DOC-001",
                "retention_policy": "RETP-001",
                "status": "published",
                "retention_until": datetime.now(UTC) + timedelta(days=30),
                "is_deleted": False,
            }
        ]
        if query.get("retention_policy") == "RETP-001"
        else []
    )
    mock_document_repo.return_value = document_repo

    response = client.get("/api/v1/retention-policies", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["summary"] == {
        "total_policy_count": 2,
        "active_policy_count": 1,
        "inactive_policy_count": 1,
        "system_policy_count": 1,
        "approval_required_count": 1,
        "mapped_category_count": 1,
        "expiring_document_count": 1,
    }
    assert payload["data"][0]["status_badge"] == "expiry_review_required"
    assert payload["data"][0]["recommended_action"] == "review_disposal_queue"
    assert "review_expiring_documents" in payload["data"][0]["available_actions"]
    assert payload["data"][0]["scope_summary"]["linked_category_count"] == 1
    assert payload["data"][1]["status_badge"] == "inactive"


@patch("oneerp_gateway_app.routes.retention_policies._get_document_repo")
@patch("oneerp_gateway_app.routes.retention_policies._get_category_repo")
@patch("oneerp_gateway_app.routes.retention_policies._get_repo")
def test_보존정책_상세요약은_연결분류와_만료현황을_반환한다(
    mock_repo: MagicMock,
    mock_category_repo: MagicMock,
    mock_document_repo: MagicMock,
) -> None:
    """상세 summary는 연결 분류, 문서 현황, 컴플라이언스 필드를 함께 제공해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "RETP-001",
        "policy_name": "계약서 10년",
        "description": "주요 계약 원본 보관",
        "retention_years": 10,
        "retention_months": 0,
        "action_on_expiry": "review",
        "requires_approval": True,
        "legal_basis": "상법 제33조",
        "is_system": False,
        "is_active": True,
    }
    mock_repo.return_value = repo

    category_repo = MagicMock()
    category_repo.find_many.return_value = [
        {
            "_id": "DC-001",
            "name": "계약 문서",
            "default_retention_policy": "RETP-001",
            "default_security_level": "confidential",
        }
    ]
    mock_category_repo.return_value = category_repo

    nearest_expiry = datetime.now(UTC) + timedelta(days=14)
    document_repo = MagicMock()
    document_repo.find_many.return_value = [
        {
            "_id": "DOC-001",
            "title": "공급 계약서",
            "retention_policy": "RETP-001",
            "status": "published",
            "retention_until": nearest_expiry,
            "is_deleted": False,
        }
    ]
    mock_document_repo.return_value = document_repo

    response = client.get(
        "/api/v1/retention-policies/RETP-001/summary", headers=TENANT_ADMIN_HEADERS
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "expiry_review_required"
    assert payload["scope_summary"]["retention_period_label"] == "10년"
    assert payload["category_summary"] == {
        "linked_category_count": 1,
        "linked_category_ids": ["DC-001"],
        "linked_category_names": ["계약 문서"],
        "default_security_levels": ["confidential"],
    }
    assert payload["document_summary"]["expiring_document_count"] == 1
    assert payload["document_summary"]["nearest_expiry_date"] == nearest_expiry.date().isoformat()
    assert payload["compliance_summary"] == {
        "action_on_expiry": "review",
        "requires_approval": True,
        "legal_basis": "상법 제33조",
        "is_system": False,
    }
    assert payload["recommended_action"] == "review_disposal_queue"


@patch("oneerp_gateway_app.routes.retention_policies._get_document_repo")
@patch("oneerp_gateway_app.routes.retention_policies._get_category_repo")
@patch("oneerp_gateway_app.routes.retention_policies._get_repo")
def test_사용중인_보존정책은_삭제할_수_없다(
    mock_repo: MagicMock,
    mock_category_repo: MagicMock,
    mock_document_repo: MagicMock,
) -> None:
    """문서 분류 또는 문서가 연결된 정책은 삭제를 차단해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "RETP-001",
        "policy_name": "세무 서류 5년",
        "retention_years": 5,
        "retention_months": 0,
        "action_on_expiry": "review",
        "requires_approval": True,
        "legal_basis": "국세기본법 제85조의3",
        "is_system": False,
        "is_active": True,
    }
    mock_repo.return_value = repo

    category_repo = MagicMock()
    category_repo.find_many.return_value = [
        {"_id": "DC-001", "default_retention_policy": "RETP-001"}
    ]
    mock_category_repo.return_value = category_repo

    document_repo = MagicMock()
    document_repo.find_many.return_value = []
    mock_document_repo.return_value = document_repo

    response = client_no_raise.delete(
        "/api/v1/retention-policies/RETP-001",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "연결된 문서 분류 또는 문서가 있는 보존 정책은 삭제할 수 없습니다"
    )
    repo.delete_by_id.assert_not_called()
