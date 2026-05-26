"""워크플로우 엔진 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_core.workflow.engine import TransitionOption, TransitionResult
from oneerp_gateway_app.routes.workflow_engine import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더
MANAGER_HEADERS: dict[str, str] = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "manager-1",
    "X-User-Roles": "manager",
    "X-User-Tier": "regular",
    "X-User-Permissions": "*:*",
}


def _mock_service() -> MagicMock:
    """WorkflowService 모의 객체를 생성한다."""
    svc = MagicMock()
    svc.apply_transition.return_value = TransitionResult(
        success=True,
        from_state="draft",
        to_state="pending_approval",
        transition_name="draft → pending_approval",
    )
    svc.get_available_actions.return_value = [
        TransitionOption(name="draft → pending_approval", to_state="pending_approval"),
    ]
    return svc


@patch("oneerp_gateway_app.routes.workflow_engine._get_workflow_service")
def test_상태_전이_실행_성공(mock_get_svc: MagicMock) -> None:
    """POST /apply로 상태 전이를 성공적으로 실행한다."""
    mock_get_svc.return_value = _mock_service()
    response = client.post(
        "/api/v1/workflow/purchase_order/PO-001/apply",
        json={"target_state": "pending_approval"},
        headers=MANAGER_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["from_state"] == "draft"
    assert data["to_state"] == "pending_approval"


@patch("oneerp_gateway_app.routes.workflow_engine._get_workflow_service")
def test_상태_전이_워크플로우_오류(mock_get_svc: MagicMock) -> None:
    """워크플로우 오류 시 400을 반환한다."""
    from oneerp_core.workflow import WorkflowError

    svc = MagicMock()
    svc.apply_transition.side_effect = WorkflowError("테스트 오류")
    mock_get_svc.return_value = svc
    response = client.post(
        "/api/v1/workflow/purchase_order/PO-999/apply",
        json={"target_state": "pending_approval"},
        headers=MANAGER_HEADERS,
    )
    assert response.status_code == 400
    assert "workflow_error" in response.json()["error"]


@patch("oneerp_gateway_app.routes.workflow_engine._get_workflow_service")
def test_가능한_액션_조회_성공(mock_get_svc: MagicMock) -> None:
    """GET /actions로 가능한 액션 목록을 조회한다."""
    mock_get_svc.return_value = _mock_service()
    response = client.get(
        "/api/v1/workflow/purchase_order/PO-001/actions",
        headers=MANAGER_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["doc_id"] == "PO-001"
    assert data["doc_type"] == "purchase_order"
    assert len(data["actions"]) == 1
    assert data["actions"][0]["to_state"] == "pending_approval"


@patch("oneerp_gateway_app.routes.workflow_engine._get_workflow_service")
def test_가능한_액션_조회_워크플로우_오류(mock_get_svc: MagicMock) -> None:
    """문서가 없을 때 400을 반환한다."""
    from oneerp_core.workflow import WorkflowError

    svc = MagicMock()
    svc.get_available_actions.side_effect = WorkflowError("문서를 찾을 수 없습니다")
    mock_get_svc.return_value = svc
    response = client.get(
        "/api/v1/workflow/purchase_order/PO-999/actions",
        headers=MANAGER_HEADERS,
    )
    assert response.status_code == 400
