"""결재라인(ApprovalLine) CRUD 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.approval_lines import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더 — approval_lines 라우트는 CurrentUserDep 사용
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.approval_lines._get_repo")
@patch("oneerp_gateway_app.routes.approval_lines.generate_name", return_value="AL-2026-00001")
def test_결재라인_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = []
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-lines/",
        json={"template": "AT-001", "sequence": 1, "approver_role": "팀장"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["approval_line_id"] == "AL-2026-00001"


@patch("oneerp_gateway_app.routes.approval_lines._get_repo")
def test_결재라인_목록은_단계요약과_워크벤치_요약을_반환한다(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "AL-001",
            "template": "AT-001",
            "sequence": 1,
            "approver": "team-lead-001",
            "approver_role": "team_lead",
            "approval_type": "consensus",
            "pre_approval_roles": [],
            "condition": "amount >= 1000000",
        },
        {
            "_id": "AL-002",
            "template": "AT-001",
            "sequence": 1,
            "approver": "legal-001",
            "approver_role": "legal_manager",
            "approval_type": "consensus",
            "pre_approval_roles": [],
            "condition": "amount >= 1000000",
        },
        {
            "_id": "AL-003",
            "template": "AT-001",
            "sequence": 2,
            "approver": "director-001",
            "approver_role": "director",
            "approval_type": "single",
            "pre_approval_roles": ["director"],
            "condition": "",
        },
    ]
    repo.count.return_value = 3
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/approval-lines/?template=AT-001&page=1&page_size=10",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["summary"] == {
        "template_count": 1,
        "step_count": 2,
        "consensus_step_count": 1,
        "pre_approval_step_count": 1,
        "conditional_step_count": 1,
    }
    assert payload["data"][0]["approval_mode_badge"] == "consensus"
    assert payload["data"][0]["step_summary"] == {
        "template": "AT-001",
        "sequence": 1,
        "approver_count": 2,
        "approval_mode": "consensus",
        "pre_approval_enabled": False,
        "condition": "amount >= 1000000",
    }
    assert payload["data"][0]["available_actions"] == ["edit", "reorder", "delete"]
    repo.find_many.assert_called_once_with(
        {"template": "AT-001"},
        skip=0,
        limit=10,
        sort=[("sequence", 1), ("created_at", 1)],
    )
    repo.count.assert_called_once_with({"template": "AT-001"})


@patch("oneerp_gateway_app.routes.approval_lines._get_repo")
def test_결재라인_상세는_단계요약과_가용액션을_반환한다(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.side_effect = [
        {
            "_id": "AL-002",
            "template": "AT-001",
            "sequence": 1,
            "approver": "legal-001",
            "approver_role": "legal_manager",
            "approval_type": "consensus",
            "pre_approval_roles": [],
            "condition": "amount >= 1000000",
        }
    ]
    repo.find_many.return_value = [
        {
            "_id": "AL-001",
            "template": "AT-001",
            "sequence": 1,
            "approver": "team-lead-001",
            "approver_role": "team_lead",
            "approval_type": "consensus",
            "pre_approval_roles": [],
            "condition": "amount >= 1000000",
        },
        {
            "_id": "AL-002",
            "template": "AT-001",
            "sequence": 1,
            "approver": "legal-001",
            "approver_role": "legal_manager",
            "approval_type": "consensus",
            "pre_approval_roles": [],
            "condition": "amount >= 1000000",
        },
    ]
    mock_repo.return_value = repo

    response = client.get("/api/v1/approval-lines/AL-002", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_mode_badge"] == "consensus"
    assert payload["step_summary"] == {
        "template": "AT-001",
        "sequence": 1,
        "approver_count": 2,
        "approval_mode": "consensus",
        "pre_approval_enabled": False,
        "condition": "amount >= 1000000",
    }
    assert payload["available_actions"] == ["edit", "reorder", "delete"]


@patch("oneerp_gateway_app.routes.approval_lines._get_repo")
def test_결재라인_생성시_동일순서_중복결재자_거부(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "AL-001",
            "template": "AT-001",
            "sequence": 1,
            "approver": "team-lead-001",
            "approver_role": "team_lead",
            "approval_type": "consensus",
            "pre_approval_roles": [],
        }
    ]
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/approval-lines/",
        json={
            "template": "AT-001",
            "sequence": 1,
            "approver": "team-lead-001",
            "approver_role": "team_lead",
            "approval_type": "consensus",
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-APR-010"


@patch("oneerp_gateway_app.routes.approval_lines._get_repo")
def test_결재라인_생성시_동일순서_결재유형혼용_거부(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "AL-001",
            "template": "AT-001",
            "sequence": 1,
            "approver": "team-lead-001",
            "approver_role": "team_lead",
            "approval_type": "consensus",
            "pre_approval_roles": [],
        }
    ]
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/approval-lines/",
        json={
            "template": "AT-001",
            "sequence": 1,
            "approver": "director-001",
            "approver_role": "director",
            "approval_type": "single",
            "pre_approval_roles": ["director"],
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-APR-011"


@patch("oneerp_gateway_app.routes.approval_lines._get_repo")
def test_결재라인_조회_미존재_404(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/approval-lines/NOT-EXIST",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 404
