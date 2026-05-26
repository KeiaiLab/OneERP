"""결재템플릿(ApprovalTemplate) CRUD 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.approval_templates import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더 — approval_templates 라우트는 CurrentUserDep 사용
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.approval_templates._get_repo")
@patch("oneerp_gateway_app.routes.approval_templates.generate_name", return_value="AT-2026-00001")
def test_결재템플릿_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/approval-templates/",
        json={
            "template_name": "구매결재",
            "document_type": "PurchaseOrder",
            "steps": [
                {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
            ],
        },
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["approval_template_id"] == "AT-2026-00001"


def test_결재템플릿_중복_필드키_거부() -> None:
    response = client.post(
        "/api/v1/approval-templates/",
        json={
            "template_name": "중복 필드",
            "document_type": "ExpenseClaim",
            "steps": [
                {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
            ],
            "form_fields": [
                {"field_key": "expense_amount", "label": "금액"},
                {"field_key": "expense_amount", "label": "총 금액"},
            ],
        },
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 422
    assert response.json()["error"] == "ERR-APR-006"


def test_결재템플릿_중복_바인딩타깃_거부() -> None:
    response = client.post(
        "/api/v1/approval-templates/",
        json={
            "template_name": "중복 바인딩",
            "document_type": "ExpenseClaim",
            "steps": [
                {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
            ],
            "data_binding_fields": [
                {"target_field": "총금액", "source_field": "total_amount"},
                {"target_field": "총금액", "source_field": "approved_amount"},
            ],
        },
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 422
    assert response.json()["error"] == "ERR-APR-007"


def test_결재템플릿_빈_단계_거부() -> None:
    response = client.post(
        "/api/v1/approval-templates/",
        json={"template_name": "단계 없음", "document_type": "ExpenseClaim", "steps": []},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 422


def test_결재템플릿_프리셋_목록_조회() -> None:
    response = client.get(
        "/api/v1/approval-templates/presets",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    codes = {preset["preset_code"] for preset in body["data"]}
    assert {"general-proposal", "expense-claim", "purchase-request"} <= codes


@patch("oneerp_gateway_app.routes.approval_templates._get_repo")
@patch("oneerp_gateway_app.routes.approval_templates.generate_name", return_value="AT-2026-00011")
def test_결재템플릿_프리셋으로_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    repo = MagicMock()
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-templates/presets/expense-claim",
        json={"template_name": "경비청구 표준"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    inserted_doc = repo.insert.call_args.args[0]
    assert inserted_doc.template_code == "expense-claim"
    assert inserted_doc.form_fields[0].field_key == "expense_date"
    assert inserted_doc.data_binding_fields[0].target_field == "신청자"


@patch("oneerp_gateway_app.routes.approval_templates._get_repo")
@patch("oneerp_gateway_app.routes.approval_templates.generate_name", return_value="AT-2026-00021")
def test_결재템플릿_복제_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "AT-BASE-001",
        "template_name": "구매요청 표준",
        "document_type": "PurchaseRequest",
        "template_code": "purchase-request",
        "description": "표준 구매요청 양식",
        "steps": [
            {"step": 1, "approver_role": "team_lead", "approver": "manager-001"},
        ],
        "form_fields": [
            {
                "field_key": "request_reason",
                "label": "요청 사유",
                "field_type": "textarea",
                "required": True,
            },
        ],
        "data_binding_fields": [
            {"target_field": "요청자", "source_field": "requester_name"},
        ],
    }
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/approval-templates/AT-BASE-001/clone",
        json={"template_name": "구매요청 표준 복사본"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    inserted_doc = repo.insert.call_args.args[0]
    assert inserted_doc.template_name == "구매요청 표준 복사본"
    assert inserted_doc.form_fields[0].field_key == "request_reason"
    assert inserted_doc.data_binding_fields[0].target_field == "요청자"


@patch("oneerp_gateway_app.routes.approval_templates._get_repo")
def test_결재템플릿_목록_조회(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "AT-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/approval-templates/?page=1&page_size=10",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_gateway_app.routes.approval_templates._get_repo")
def test_결재템플릿_조회_미존재_404(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/approval-templates/NOT-EXIST",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 404


@patch("oneerp_gateway_app.routes.approval_templates._get_approval_line_repo")
@patch("oneerp_gateway_app.routes.approval_templates._get_repo")
def test_결재템플릿_결재선_참조중_삭제_거부(
    mock_repo: MagicMock,
    mock_line_repo: MagicMock,
) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "AT-001", "template_name": "구매요청 표준"}
    line_repo = MagicMock()
    line_repo.count.return_value = 1
    mock_repo.return_value = repo
    mock_line_repo.return_value = line_repo

    response = client.delete(
        "/api/v1/approval-templates/AT-001",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-APR-008"
