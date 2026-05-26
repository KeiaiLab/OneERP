"""사용자(User) 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.users import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# Tenant Admin 헤더 — users 라우트는 require_tenant_admin() 의존성 사용
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.services.user_service._get_company_repo")
@patch("oneerp_gateway_app.services.user_service._get_repo")
@patch("oneerp_gateway_app.services.user_service.generate_name")
def test_사용자_생성은_초대상태와_해시를_저장한다(
    mock_name: MagicMock, mock_repo: MagicMock, mock_company_repo: MagicMock
) -> None:
    """사용자 생성 시 초대/OIDC 메타데이터와 비밀번호 해시를 저장해야 한다."""
    mock_name.side_effect = lambda prefix, *, tenant_id=None: (
        "USR-2026-00001"
        if tenant_id == "test-tenant"
        else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
    )
    mock_repo.return_value = MagicMock()
    company_repo = MagicMock()
    company_repo.find_by_id.return_value = {"_id": "COMP-001", "company_name": "원이알피"}
    mock_company_repo.return_value = company_repo
    response = client.post(
        "/api/v1/users/",
        json={
            "username": "admin",
            "email": "admin@oneerp.io",
            "full_name": "관리자",
            "roles": ["finance_manager"],
            "company_id": "COMP-001",
            "department_name": "재무팀",
            "auth_provider": "oidc",
            "password": "Secret123!",
        },
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["user_id"] == "USR-2026-00001"
    assert response.json()["id"] == "USR-2026-00001"
    mock_name.assert_called_once_with("USR", tenant_id="test-tenant")
    inserted_doc = mock_repo.return_value.insert.call_args.args[0]
    assert (
        inserted_doc.password_hash
        == "94e0f9bc7f5a5225bd141bad5adf9befcc112aef09b88f47a14e20b75a7bbec2"  # noqa: S105
    )
    assert inserted_doc.invitation_status == "pending"
    assert inserted_doc.auth_provider == "oidc"
    assert inserted_doc.company_id == "COMP-001"
    assert inserted_doc.department_name == "재무팀"
    assert inserted_doc.invited_by == "tenant-admin"


@patch("oneerp_gateway_app.services.user_service._get_company_repo")
@patch("oneerp_gateway_app.services.user_service._get_repo")
def test_사용자_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_repo: MagicMock, mock_company_repo: MagicMock
) -> None:
    """사용자 목록은 초대/OIDC 상태와 운영 요약을 함께 반환해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "USR-001",
            "username": "oidc-user",
            "email": "oidc@oneerp.io",
            "full_name": "OIDC 사용자",
            "roles": ["sales_user"],
            "company_id": "COMP-001",
            "department_name": "영업팀",
            "auth_provider": "oidc",
            "oidc_subject": "",
            "invitation_status": "pending",
            "is_active": True,
            "user_tier": "regular",
            "is_super_admin": False,
        }
    ]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    company_repo = MagicMock()
    company_repo.find_by_id.return_value = {"_id": "COMP-001", "company_name": "원이알피"}
    mock_company_repo.return_value = company_repo
    response = client.get(
        "/api/v1/users/?page=1&page_size=10",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    payload = response.json()
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
    assert payload["data"][0]["access_summary"]["company_name"] == "원이알피"


@patch("oneerp_gateway_app.services.user_service._get_repo")
def test_사용자_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 사용자 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/users/NOT-EXIST",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 404


@patch("oneerp_gateway_app.services.user_service._get_company_repo")
@patch("oneerp_gateway_app.services.user_service._get_repo")
def test_사용자_상세요약은_권한과_OIDC_상태를_반환한다(
    mock_repo: MagicMock, mock_company_repo: MagicMock
) -> None:
    """상세 요약은 접근 범위와 인증 상태를 함께 제공해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "USR-001",
        "username": "oidc-user",
        "email": "oidc@oneerp.io",
        "full_name": "OIDC 사용자",
        "roles": ["accounting_manager", "approver"],
        "company_id": "COMP-001",
        "department_name": "재무팀",
        "auth_provider": "oidc",
        "oidc_subject": "oidc|user-001",
        "invitation_status": "linked",
        "is_active": True,
        "user_tier": "tenant_admin",
        "is_super_admin": False,
        "last_login": "2026-04-09T10:00:00+09:00",
    }
    mock_repo.return_value = repo
    company_repo = MagicMock()
    company_repo.find_by_id.return_value = {"_id": "COMP-001", "company_name": "원이알피"}
    mock_company_repo.return_value = company_repo

    response = client.get("/api/v1/users/USR-001/summary", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "oidc_linked"
    assert payload["access_summary"] == {
        "primary_role": "accounting_manager",
        "role_count": 2,
        "company_id": "COMP-001",
        "company_name": "원이알피",
        "department_name": "재무팀",
        "user_tier": "tenant_admin",
        "is_super_admin": False,
    }
    assert payload["auth_summary"] == {
        "auth_provider": "oidc",
        "oidc_subject": "oidc|user-001",
        "invitation_status": "linked",
        "last_login": "2026-04-09T10:00:00+09:00",
    }
    assert "review_access_scope" in payload["available_actions"]


@patch("oneerp_gateway_app.services.user_service._get_repo")
def test_활성_사용자는_삭제할_수_없다(mock_repo: MagicMock) -> None:
    """활성 사용자는 먼저 비활성화해야 삭제할 수 있다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "USR-001",
        "username": "active-user",
        "is_active": True,
    }
    mock_repo.return_value = repo

    response = client.delete("/api/v1/users/USR-001", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 422
    assert response.json()["detail"] == "활성 사용자는 삭제할 수 없습니다. 먼저 비활성화하세요"
    repo.delete_by_id.assert_not_called()
