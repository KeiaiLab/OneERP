"""문서 관리 라우트 워크벤치 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_documents_app.routes.document_routes import router

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

    def find_many(
        self,
        query: dict | None = None,
        *,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        data = self._docs
        if query:
            filtered: list[dict] = []
            for doc in data:
                matched = True
                for key, expected in query.items():
                    actual = doc.get(key)
                    if isinstance(expected, dict) and "$in" in expected:
                        if actual not in expected["$in"]:
                            matched = False
                            break
                    elif actual != expected:
                        matched = False
                        break
                if matched:
                    filtered.append(doc)
            data = filtered
        if sort:
            for field, direction in reversed(sort):
                data = sorted(
                    data,
                    key=lambda item: item.get(field) or "",
                    reverse=direction < 0,
                )
        return data[skip : skip + limit]

    def count(self, query: dict | None = None) -> int:
        return len(self.find_many(query))

    def find_by_id(self, doc_id: str) -> dict | None:
        return next((doc for doc in self._docs if doc.get("_id") == doc_id), None)


@patch("oneerp_documents_app.routes.document_routes._get_audit_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_version_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_signature_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_share_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_category_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_doc_repo", create=True)
def test_문서_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_doc_repo: MagicMock,
    mock_category_repo: MagicMock,
    mock_share_repo: MagicMock,
    mock_signature_repo: MagicMock,
    mock_version_repo: MagicMock,
    mock_audit_repo: MagicMock,
) -> None:
    now = datetime(2026, 4, 10, 9, 0, tzinfo=UTC)
    mock_doc_repo.return_value = _FakeRepo(
        [
            {
                "_id": "DOC-001",
                "title": "영업 운영 지침",
                "summary": "승인된 지침서",
                "status": "published",
                "category": "DC-001",
                "author": "EMP-001",
                "department": "DEPT-SALES",
                "security_level": "internal",
                "version": 3,
                "is_locked": False,
                "retention_until": now + timedelta(days=20),
                "created_at": now,
                "updated_at": now,
            },
            {
                "_id": "DOC-002",
                "title": "영업 초안 메모",
                "summary": "작성 중",
                "status": "draft",
                "category": "DC-001",
                "author": "EMP-002",
                "department": "DEPT-SALES",
                "security_level": "internal",
                "version": 1,
                "is_locked": True,
                "locked_by": "EMP-002",
                "retention_until": None,
                "created_at": now - timedelta(days=1),
                "updated_at": now - timedelta(days=1),
            },
        ]
    )
    mock_category_repo.return_value = _FakeRepo(
        [{"_id": "DC-001", "name": "영업 문서", "default_security_level": "internal"}]
    )
    mock_share_repo.return_value = _FakeRepo(
        [
            {
                "_id": "DS-001",
                "document_id": "DOC-001",
                "share_type": "external_link",
                "expires_at": now + timedelta(days=7),
                "is_active": True,
            }
        ]
    )
    mock_signature_repo.return_value = _FakeRepo(
        [{"_id": "SG-001", "document_id": "DOC-001", "is_valid": True, "signed_at": now}]
    )
    mock_version_repo.return_value = _FakeRepo(
        [
            {
                "_id": "DV-001",
                "document_id": "DOC-001",
                "version_no": 3,
                "change_summary": "최종본",
            },
            {"_id": "DV-002", "document_id": "DOC-002", "version_no": 1, "change_summary": "초안"},
        ]
    )
    mock_audit_repo.return_value = _FakeRepo([])

    response = client.get(
        "/api/v1/documents",
        params={"q": "영업", "status": "published"},
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "draft_count": 0,
        "review_count": 0,
        "approved_count": 0,
        "published_count": 1,
        "archived_count": 0,
        "disposed_count": 0,
        "locked_count": 0,
        "shared_externally_count": 1,
        "signed_count": 1,
        "retention_due_soon_count": 1,
    }
    row = payload["data"][0]
    assert row["status_badge"] == "published_signed"
    assert row["recommended_action"] == "review_external_shares"
    assert row["share_summary"]["external_link_count"] == 1
    assert row["version_summary"]["total_versions"] == 1


@patch("oneerp_documents_app.routes.document_routes._get_audit_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_version_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_signature_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_share_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_category_repo", create=True)
@patch("oneerp_documents_app.routes.document_routes._get_doc_repo", create=True)
def test_문서_상세요약은_버전_공유_서명_감사_맥락을_반환한다(
    mock_doc_repo: MagicMock,
    mock_category_repo: MagicMock,
    mock_share_repo: MagicMock,
    mock_signature_repo: MagicMock,
    mock_version_repo: MagicMock,
    mock_audit_repo: MagicMock,
) -> None:
    now = datetime(2026, 4, 10, 9, 0, tzinfo=UTC)
    mock_doc_repo.return_value = _FakeRepo(
        [
            {
                "_id": "DOC-001",
                "title": "인사 규정",
                "summary": "배포된 최신 규정",
                "status": "published",
                "category": "DC-002",
                "author": "EMP-HR-001",
                "department": "DEPT-HR",
                "security_level": "confidential",
                "version": 4,
                "is_locked": False,
                "retention_until": now + timedelta(days=365),
                "created_at": now - timedelta(days=10),
                "updated_at": now,
            }
        ]
    )
    mock_category_repo.return_value = _FakeRepo([{"_id": "DC-002", "name": "인사 규정"}])
    mock_share_repo.return_value = _FakeRepo(
        [
            {
                "_id": "DS-001",
                "document_id": "DOC-001",
                "share_type": "department",
                "target_department": "DEPT-HR",
                "is_active": True,
            },
            {
                "_id": "DS-002",
                "document_id": "DOC-001",
                "share_type": "external_link",
                "expires_at": now + timedelta(days=5),
                "is_active": True,
            },
        ]
    )
    mock_signature_repo.return_value = _FakeRepo(
        [
            {
                "_id": "SG-001",
                "document_id": "DOC-001",
                "is_valid": True,
                "signer": "legal-lead",
                "signed_at": now - timedelta(days=1),
            }
        ]
    )
    mock_version_repo.return_value = _FakeRepo(
        [
            {"_id": "DV-001", "document_id": "DOC-001", "version_no": 1, "change_summary": "초안"},
            {
                "_id": "DV-004",
                "document_id": "DOC-001",
                "version_no": 4,
                "change_summary": "최종 개정",
            },
        ]
    )
    mock_audit_repo.return_value = _FakeRepo(
        [
            {
                "_id": "AL-001",
                "document_id": "DOC-001",
                "action": "publish",
                "actor": "legal-lead",
                "timestamp": now,
            }
        ]
    )

    response = client.get("/api/v1/documents/DOC-001/summary", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "published_signed"
    assert payload["lifecycle_summary"]["status"] == "published"
    assert payload["version_summary"] == {
        "current_version": 4,
        "total_versions": 2,
        "latest_change_summary": "최종 개정",
    }
    assert payload["sharing_summary"] == {
        "active_share_count": 2,
        "department_share_count": 1,
        "external_link_count": 1,
        "latest_external_expiry": "2026-04-15T09:00:00+00:00",
    }
    assert payload["signature_summary"] == {
        "valid_signature_count": 1,
        "latest_signer": "legal-lead",
        "last_signed_at": "2026-04-09T09:00:00+00:00",
    }
    assert payload["audit_summary"] == {
        "event_count": 1,
        "last_action": "publish",
        "last_actor": "legal-lead",
    }
    assert payload["available_actions"] == [
        "view_versions",
        "manage_shares",
        "verify_signature",
        "archive",
    ]
