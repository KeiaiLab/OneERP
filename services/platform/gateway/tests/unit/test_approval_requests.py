"""결재요청(ApprovalRequest) CRUD 테스트 — Transaction 패턴."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.approval_requests import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더 — approval_requests 라우트는 CurrentUserDep 사용
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}

DIRECTOR_HEADERS = {
    **TENANT_ADMIN_HEADERS,
    "X-User-Sub": "director-001",
    "X-User-Roles": "director",
}


@patch("oneerp_gateway_app.routes.approval_requests.ApprovalService")
def test_결재요청_생성_정상(mock_service_cls: MagicMock) -> None:
    service = MagicMock()
    service.create_request.return_value = {
        "request_id": "AR-2026-00001",
        "status": "pending",
        "current_step": 1,
        "total_steps": 2,
    }
    mock_service_cls.return_value = service
    response = client.post(
        "/api/v1/approval-requests/",
        json={
            "document_type": "PurchaseOrder",
            "document_id": "PO-2026-00001",
            "requester": "홍길동",
        },
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["request_id"] == "AR-2026-00001"
    assert response.json()["total_steps"] == 2
    service.create_request.assert_called_once_with(
        document_type="PurchaseOrder",
        document_id="PO-2026-00001",
        requester="홍길동",
    )


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_목록_조회(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "AR-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/approval-requests/?page=1&page_size=10",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_조회_미존재_404(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/approval-requests/NOT-EXIST",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 404


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_제출_정상(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "AR-001", "status": "pending"}
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-requests/AR-001/submit",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert "제출" in response.json()["message"]


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_제출_상태오류(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "AR-001", "status": "submitted"}
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-requests/AR-001/submit",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 400


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_취소_정상(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    # BR-APPR-015: requester가 현재 사용자(tenant-admin)와 일치해야 취소 가능
    repo.find_by_id.return_value = {
        "_id": "AR-001",
        "status": "pending",
        "requester": "tenant-admin",
    }
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-requests/AR-001/cancel",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert "취소" in response.json()["message"]


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_취소_상태오류(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "AR-001",
        "status": "cancelled",
        "requester": "tenant-admin",
    }
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-requests/AR-001/cancel",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 400


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_취소_기안자_아닌_사용자_거부(mock_repo: MagicMock) -> None:
    """BR-APPR-015: 기안자가 아닌 사용자가 취소하면 403 에러."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "AR-001",
        "status": "pending",
        "requester": "다른사용자",  # 현재 사용자(tenant-admin)와 불일치
    }
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-requests/AR-001/cancel",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 403
    assert "기안자" in response.json()["detail"]


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_목록이_대기함_요약과_가능액션을_반환(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    docs = [
        {
            "_id": "AR-001",
            "status": "submitted",
            "requester": "requester-001",
            "current_step": 1,
            "approval_lines": [
                {
                    "step": 1,
                    "approver": "director-001",
                    "approver_role": "director",
                    "status": "pending",
                    "approval_type": "single",
                    "pre_approval_roles": ["director"],
                }
            ],
        },
        {
            "_id": "AR-002",
            "status": "submitted",
            "requester": "director-001",
            "current_step": 2,
            "approval_lines": [
                {"step": 1, "approver": "manager-001", "status": "approved"},
                {
                    "step": 2,
                    "approver": "finance-001",
                    "approver_role": "finance_manager",
                    "status": "pending",
                    "approval_type": "consensus",
                },
                {
                    "step": 2,
                    "approver": "legal-001",
                    "approver_role": "legal_manager",
                    "status": "pending",
                    "approval_type": "consensus",
                },
            ],
        },
        {
            "_id": "AR-003",
            "status": "approved",
            "requester": "requester-002",
            "current_step": 1,
            "approval_lines": [
                {"step": 1, "approver": "director-001", "status": "approved"},
            ],
        },
    ]
    repo.count.return_value = len(docs)
    repo.find_many.return_value = docs
    mock_repo.return_value = repo

    response = client.get(
        "/api/v1/approval-requests?page=1&page_size=10",
        headers=DIRECTOR_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {
        "by_status": {
            "pending": 0,
            "submitted": 2,
            "approved": 1,
            "rejected": 0,
            "cancelled": 0,
        },
        "waiting_on_me_count": 1,
        "my_requested_count": 1,
        "consensus_pending_count": 1,
    }

    actionable = next(doc for doc in payload["data"] if doc["_id"] == "AR-001")
    assert actionable["waiting_on_me"] is True
    assert actionable["status_badge"] == "pending_approval"
    assert actionable["available_actions"] == ["approve", "reject", "delegate", "pre_approve"]

    consensus = next(doc for doc in payload["data"] if doc["_id"] == "AR-002")
    assert consensus["status_badge"] == "consensus_pending"
    assert consensus["current_step_summary"]["pending_approver_count"] == 2


@patch("oneerp_gateway_app.routes.approval_requests._get_repo")
def test_결재요청_상세가_현재단계와_처리액션을_노출(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "AR-010",
        "status": "submitted",
        "requester": "requester-001",
        "document_type": "ExpenseClaim",
        "document_id": "EXP-001",
        "current_step": 2,
        "approval_lines": [
            {"step": 1, "approver": "manager-001", "status": "approved"},
            {
                "step": 2,
                "approver": "director-001",
                "approver_role": "director",
                "status": "pending",
                "approval_type": "single",
                "pre_approval_roles": ["director"],
            },
        ],
    }
    mock_repo.return_value = repo

    response = client.get(
        "/api/v1/approval-requests/AR-010",
        headers=DIRECTOR_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "pending_approval"
    assert payload["waiting_on_me"] is True
    assert payload["current_step_summary"] == {
        "step": 2,
        "approval_type": "single",
        "pending_approver_count": 1,
        "approvers": [
            {
                "approver": "director-001",
                "approver_role": "director",
                "status": "pending",
                "is_current_user": True,
                "can_pre_approve": True,
            }
        ],
    }
    assert payload["available_actions"] == ["approve", "reject", "delegate", "pre_approve"]
