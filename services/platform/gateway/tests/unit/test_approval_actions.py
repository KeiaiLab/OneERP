"""결재이력(ApprovalAction) 감사 워크벤치 테스트."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.approval_actions import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


class _FakeRepo:
    """간단한 메모리 저장소."""

    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    @staticmethod
    def _matches(doc: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = doc.get(key)
            if isinstance(expected, dict):
                if "$in" in expected and actual not in expected["$in"]:
                    return False
                comparable = actual
                if isinstance(actual, date) and not isinstance(actual, datetime):
                    comparable = datetime.combine(actual, datetime.min.time(), tzinfo=UTC)
                if "$gte" in expected and comparable < expected["$gte"]:
                    return False
                if "$lte" in expected and comparable > expected["$lte"]:
                    return False
                continue
            if actual != expected:
                return False
        return True

    def find_many(
        self,
        query: dict | None = None,
        *,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        data = [doc for doc in self._docs if self._matches(doc, query or {})]
        if sort:
            for field, direction in reversed(sort):
                data.sort(
                    key=lambda item: item.get(field) or datetime.min.replace(tzinfo=UTC),
                    reverse=direction < 0,
                )
        return data[skip : skip + limit]

    def count(self, query: dict | None = None) -> int:
        return len([doc for doc in self._docs if self._matches(doc, query or {})])

    def find_by_id(self, doc_id: str) -> dict | None:
        return next((doc for doc in self._docs if doc.get("_id") == doc_id), None)

    def insert(self, doc: object) -> str:
        payload = dict(doc.model_dump())  # type: ignore[attr-defined]
        self._docs.append(payload)
        return str(payload.get("_id", ""))


@patch("oneerp_gateway_app.routes.approval_actions._get_request_repo", create=True)
@patch("oneerp_gateway_app.routes.approval_actions._get_repo")
@patch("oneerp_gateway_app.routes.approval_actions.generate_name", return_value="AA-2026-00001")
def test_결재이력_생성_정상(
    mock_name: MagicMock,
    mock_repo: MagicMock,
    mock_request_repo: MagicMock,
) -> None:
    mock_repo.return_value = _FakeRepo([])
    request_repo = MagicMock()
    request_repo.find_by_id.return_value = {
        "_id": "AR-001",
        "current_step": 1,
        "status": "pending",
        "document_type": "PurchaseOrder",
        "document_id": "PO-001",
    }
    mock_request_repo.return_value = request_repo

    response = client.post(
        "/api/v1/approval-actions/",
        json={
            "approval_request": "AR-001",
            "action_type": "approve",
            "actor": "김부장",
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 201
    assert response.json()["approval_action_id"] == "AA-2026-00001"


@patch("oneerp_gateway_app.routes.approval_actions._get_request_repo", create=True)
@patch("oneerp_gateway_app.routes.approval_actions._get_repo")
@patch("oneerp_gateway_app.routes.approval_actions.generate_name", return_value="AA-2026-00999")
def test_결재승인_후속액션_디스패치_정상(
    mock_name: MagicMock,
    mock_repo: MagicMock,
    mock_request_repo: MagicMock,
) -> None:
    """POST /api/v1/approval-actions/dispatch — 승인 완료 후속 액션을 감사 이력으로 남긴다."""
    assert mock_name is not None
    action_repo = _FakeRepo([])
    request_repo = MagicMock()
    request_repo.find_by_id.return_value = {
        "_id": "AR-001",
        "current_step": 2,
        "status": "approved",
        "document_type": "PurchaseOrder",
        "document_id": "PO-001",
    }
    mock_repo.return_value = action_repo
    mock_request_repo.return_value = request_repo

    response = client.post(
        "/api/v1/approval-actions/dispatch",
        json={
            "approval_request_id": "AR-001",
            "target_doctype": "PurchaseOrder",
            "target_doc_id": "PO-001",
            "approver": "director-001",
            "tenant_id": "test-tenant",
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_action_id"] == "AA-2026-00999"
    inserted = action_repo._docs[0]
    assert inserted["approval_request"] == "AR-001"
    assert inserted["action_type"] == "approve"
    assert inserted["document_type"] == "PurchaseOrder"
    assert inserted["document_id"] == "PO-001"
    assert inserted["actor"] == "director-001"


@patch("oneerp_gateway_app.routes.approval_actions._get_request_repo", create=True)
@patch("oneerp_gateway_app.routes.approval_actions._get_repo")
def test_결재이력_목록은_워크벤치_배지와_감사요약을_반환한다(
    mock_repo: MagicMock,
    mock_request_repo: MagicMock,
) -> None:
    action_repo = _FakeRepo(
        [
            {
                "_id": "AA-001",
                "approval_request": "AR-001",
                "action_type": "approve",
                "actor": "manager-001",
                "comment": "1차 승인",
                "acted_at": datetime(2026, 3, 10, 9, 0, tzinfo=UTC),
                "action_date": date(2026, 3, 10),
                "step": 1,
                "request_status": "pending",
                "tenant_id": "test-tenant",
            },
            {
                "_id": "AA-002",
                "approval_request": "AR-001",
                "action_type": "delegate",
                "actor": "finance-manager-001",
                "comment": "담당 임원에게 위임",
                "delegate_to": "director-001",
                "acted_at": datetime(2026, 3, 10, 10, 0, tzinfo=UTC),
                "action_date": date(2026, 3, 10),
                "step": 2,
                "request_status": "submitted",
                "tenant_id": "test-tenant",
            },
        ]
    )
    request_repo = _FakeRepo(
        [
            {
                "_id": "AR-001",
                "document_type": "ExpenseClaim",
                "document_id": "EC-001",
                "requester": "employee-001",
                "status": "submitted",
                "current_step": 2,
                "approval_lines": [
                    {"step": 1, "status": "approved"},
                    {"step": 2, "status": "pending"},
                ],
                "tenant_id": "test-tenant",
            }
        ]
    )
    mock_repo.return_value = action_repo
    mock_request_repo.return_value = request_repo

    response = client.get("/api/v1/approval-actions", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["approval_request_count"] == 1
    assert payload["summary"]["actor_counts"] == {
        "finance-manager-001": 1,
        "manager-001": 1,
    }
    assert payload["summary"]["request_status_counts"] == {
        "pending": 1,
        "submitted": 1,
    }
    row = payload["data"][0]
    assert row["action_badge"] == "delegated"
    assert row["request_status_badge"] == "submitted_review"
    assert row["delegate_summary"] == {
        "has_delegate": True,
        "delegate_to": "director-001",
    }
    assert row["request_summary"] == {
        "approval_request": "AR-001",
        "requester": "employee-001",
        "current_status": "submitted",
        "current_step": 2,
        "total_steps": 2,
        "document_type": "ExpenseClaim",
        "document_id": "EC-001",
    }
    assert row["available_actions"] == [
        "open_request",
        "open_document",
        "open_audit_report",
        "open_delegate_context",
    ]


@patch("oneerp_gateway_app.routes.approval_actions._get_repo")
def test_결재이력_조회_미존재_404(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo

    response = client.get("/api/v1/approval-actions/NOT-EXIST", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 404


@patch("oneerp_gateway_app.routes.approval_actions._get_request_repo", create=True)
@patch("oneerp_gateway_app.routes.approval_actions._get_repo")
def test_결재이력_상세는_요청문맥과_타임라인요약을_노출한다(
    mock_repo: MagicMock,
    mock_request_repo: MagicMock,
) -> None:
    action_repo = _FakeRepo(
        [
            {
                "_id": "AA-001",
                "approval_request": "AR-001",
                "action_type": "approve",
                "actor": "manager-001",
                "comment": "1차 승인",
                "acted_at": datetime(2026, 3, 10, 9, 0, tzinfo=UTC),
                "action_date": date(2026, 3, 10),
                "step": 1,
                "request_status": "pending",
                "tenant_id": "test-tenant",
            },
            {
                "_id": "AA-002",
                "approval_request": "AR-001",
                "action_type": "reject",
                "actor": "director-001",
                "comment": "예산 재검토",
                "acted_at": datetime(2026, 3, 10, 11, 0, tzinfo=UTC),
                "action_date": date(2026, 3, 10),
                "step": 2,
                "request_status": "rejected",
                "tenant_id": "test-tenant",
            },
        ]
    )
    request_repo = _FakeRepo(
        [
            {
                "_id": "AR-001",
                "document_type": "PurchaseOrder",
                "document_id": "PO-001",
                "requester": "employee-001",
                "status": "rejected",
                "current_step": 2,
                "approval_lines": [
                    {"step": 1, "status": "approved"},
                    {"step": 2, "status": "rejected"},
                ],
                "tenant_id": "test-tenant",
            }
        ]
    )
    mock_repo.return_value = action_repo
    mock_request_repo.return_value = request_repo

    response = client.get("/api/v1/approval-actions/AA-002", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["action_badge"] == "rejected"
    assert payload["request_status_badge"] == "rejected"
    assert payload["request_summary"]["current_status"] == "rejected"
    assert payload["timeline_summary"]["total_actions"] == 2
    assert payload["timeline_summary"]["action_counts"] == {"approve": 1, "reject": 1}
    assert payload["timeline_summary"]["actor_counts"] == {
        "director-001": 1,
        "manager-001": 1,
    }
    assert payload["available_actions"] == [
        "open_request",
        "open_document",
        "open_audit_report",
    ]


@patch("oneerp_gateway_app.routes.approval_actions._get_request_repo", create=True)
@patch("oneerp_gateway_app.routes.approval_actions._get_repo")
def test_결재이력_리포트는_결재자별_집계와_요청상태_분포를_제공한다(
    mock_repo: MagicMock,
    mock_request_repo: MagicMock,
) -> None:
    action_repo = _FakeRepo(
        [
            {
                "_id": "AA-001",
                "approval_request": "AR-001",
                "action_type": "approve",
                "actor": "manager-001",
                "comment": "1차 승인",
                "acted_at": datetime(2026, 3, 10, 9, 0, tzinfo=UTC),
                "action_date": date(2026, 3, 10),
                "step": 1,
                "request_status": "pending",
                "tenant_id": "test-tenant",
            },
            {
                "_id": "AA-002",
                "approval_request": "AR-001",
                "action_type": "delegate",
                "actor": "finance-manager-001",
                "comment": "부재로 위임",
                "delegate_to": "delegate-001",
                "acted_at": datetime(2026, 3, 10, 10, 0, tzinfo=UTC),
                "action_date": date(2026, 3, 10),
                "step": 2,
                "request_status": "submitted",
                "tenant_id": "test-tenant",
            },
            {
                "_id": "AA-003",
                "approval_request": "AR-002",
                "action_type": "reject",
                "actor": "director-001",
                "comment": "예산 재검토",
                "acted_at": datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
                "action_date": date(2026, 4, 1),
                "step": 1,
                "request_status": "rejected",
                "tenant_id": "test-tenant",
            },
        ]
    )
    request_repo = _FakeRepo(
        [
            {
                "_id": "AR-001",
                "document_type": "PurchaseOrder",
                "document_id": "PO-001",
                "tenant_id": "test-tenant",
            },
            {
                "_id": "AR-002",
                "document_type": "ExpenseClaim",
                "document_id": "EC-001",
                "tenant_id": "test-tenant",
            },
        ]
    )
    mock_repo.return_value = action_repo
    mock_request_repo.return_value = request_repo

    response = client.get(
        "/api/v1/approval-actions/report?from_date=2026-03-01&to_date=2026-04-30",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_actions"] == 3
    assert payload["summary"]["action_counts"] == {
        "approve": 1,
        "delegate": 1,
        "reject": 1,
    }
    assert payload["summary"]["actor_counts"] == {
        "director-001": 1,
        "finance-manager-001": 1,
        "manager-001": 1,
    }
    assert payload["summary"]["request_status_counts"] == {
        "pending": 1,
        "submitted": 1,
        "rejected": 1,
    }
    assert payload["summary"]["approval_request_count"] == 2
    assert [item["action_type"] for item in payload["timeline"]] == [
        "approve",
        "delegate",
        "reject",
    ]
