"""위임규칙(DelegationRule) 관리 API 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.delegation_rules import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)
client_no_raise = TestClient(_app, raise_server_exceptions=False)

# 인증 헤더 — delegation_rules 라우트는 CurrentUserDep 사용
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.delegation_rules._get_repo")
@patch("oneerp_gateway_app.routes.delegation_rules.generate_name", return_value="DR-2026-00001")
def test_위임규칙_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/delegation-rules/",
        json={"delegator": "김팀장", "delegate": "이대리"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["delegation_rule_id"] == "DR-2026-00001"


@patch("oneerp_gateway_app.routes.delegation_rules._get_repo")
def test_위임규칙_목록_조회(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "DR-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/delegation-rules/?page=1&page_size=10",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_gateway_app.routes.delegation_rules._get_repo")
def test_위임규칙_조회_미존재_404(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/delegation-rules/NOT-EXIST",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 404


@patch("oneerp_gateway_app.routes.delegation_rules._get_repo")
def test_위임규칙_생성시_기간역전은_검증실패(mock_repo: MagicMock) -> None:
    """종료일이 시작일보다 빠른 규칙은 저장되면 안 된다."""
    mock_repo.return_value = MagicMock()

    response = client_no_raise.post(
        "/api/v1/delegation-rules/",
        json={
            "delegator": "김팀장",
            "delegate": "이대리",
            "from_date": "2026-04-20",
            "to_date": "2026-04-10",
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"] == "위임 종료일은 시작일보다 빠를 수 없습니다"


@patch("oneerp_gateway_app.routes.delegation_rules._get_repo")
def test_위임규칙_목록은_워크벤치_배지와_범위요약을_반환한다(mock_repo: MagicMock) -> None:
    """운영자는 만료 임박/전사 적용 여부를 목록에서 바로 확인해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "DR-010",
            "delegator": "김팀장",
            "delegate": "이대리",
            "document_type": "",
            "from_date": date(2026, 4, 1),
            "to_date": date(2026, 4, 30),
            "is_active": True,
        },
        {
            "_id": "DR-011",
            "delegator": "김팀장",
            "delegate": "박대리",
            "document_type": "ExpenseClaim",
            "from_date": date(2026, 4, 1),
            "to_date": date(2026, 4, 11),
            "is_active": True,
        },
        {
            "_id": "DR-012",
            "delegator": "김팀장",
            "delegate": "최대리",
            "document_type": "PurchaseOrder",
            "from_date": date(2026, 4, 1),
            "to_date": date(2026, 4, 30),
            "is_active": False,
        },
    ]
    repo.count.return_value = 3
    mock_repo.return_value = repo

    response = client.get(
        "/api/v1/delegation-rules?as_of_date=2026-04-10",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {
        "active": 2,
        "inactive": 1,
        "expired": 0,
        "global_scope_count": 1,
        "scoped_rule_count": 2,
        "expiring_soon_count": 1,
    }
    assert payload["data"][0]["status_badge"] == "active_global"
    assert payload["data"][0]["recommended_action"] == "monitor_rule_usage"
    assert payload["data"][0]["scope_summary"]["rule_scope"] == "all_documents"
    assert payload["data"][1]["status_badge"] == "expiring_soon"
    assert payload["data"][1]["recommended_action"] == "extend_rule"
    assert payload["data"][1]["scope_summary"]["remaining_days"] == 1
    assert payload["data"][1]["available_actions"] == ["edit", "deactivate", "delete"]


@patch("oneerp_gateway_app.routes.delegation_rules._get_repo")
def test_위임규칙_상세는_범위요약과_권장액션을_반환한다(mock_repo: MagicMock) -> None:
    """상세 화면은 적용 범위/남은 일수/운영 액션을 함께 보여줘야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "DR-020",
        "delegator": "김팀장",
        "delegate": "박대리",
        "document_type": "ExpenseClaim",
        "from_date": date(2026, 4, 1),
        "to_date": date(2026, 4, 11),
        "is_active": True,
    }
    mock_repo.return_value = repo

    response = client.get(
        "/api/v1/delegation-rules/DR-020?as_of_date=2026-04-10",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "expiring_soon"
    assert payload["recommended_action"] == "extend_rule"
    assert payload["scope_summary"] == {
        "rule_scope": "document_scoped",
        "document_type": "ExpenseClaim",
        "applies_to_all_documents": False,
        "remaining_days": 1,
        "is_expiring_soon": True,
    }
    assert payload["available_actions"] == ["edit", "deactivate", "delete"]


@patch("oneerp_gateway_app.routes.delegation_rules._get_repo")
def test_겹치는_활성_위임규칙은_생성할_수_없다(mock_repo: MagicMock) -> None:
    """같은 위임자/범위에 기간이 겹치는 활성 규칙은 운영 혼선을 막기 위해 거부한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "DR-EXIST",
            "delegator": "김팀장",
            "delegate": "이대리",
            "document_type": "ExpenseClaim",
            "from_date": date(2026, 4, 1),
            "to_date": date(2026, 4, 30),
            "is_active": True,
        }
    ]
    mock_repo.return_value = repo

    response = client_no_raise.post(
        "/api/v1/delegation-rules/",
        json={
            "delegator": "김팀장",
            "delegate": "박대리",
            "document_type": "ExpenseClaim",
            "from_date": "2026-04-10",
            "to_date": "2026-04-20",
            "is_active": True,
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"] == "ERR-APR-012"
    assert (
        payload["detail"] == "같은 위임자에 대해 기간이 겹치는 활성 위임 규칙은 등록할 수 없습니다"
    )
