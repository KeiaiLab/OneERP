"""문서 공유 서비스 단위 테스트.

SC-DOC-007: 외부 링크 생성.
BR-DOC-013: 외부 공유 링크 만료일 필수.
EX-DOC-013: 외부 공유 링크 만료 검증.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_documents_app.services.document_share_service import DocumentShareService


class TestDocumentShareService:
    """DocumentShareService 테스트."""

    def test_내부_공유_생성(self, mock_collection: MagicMock) -> None:
        """내부 사용자 공유를 생성한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "published",
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentShareService("T1")
        result = svc.create_share(
            document_id="DOC-0001",
            share_type="user",
            target_user="EMP-002",
            permission="viewer",
            shared_by="EMP-001",
        )

        assert result["share_type"] == "user"
        assert result["target_user"] == "EMP-002"
        assert result["is_active"] is True
        assert result["external_link_token"] is None

    def test_외부_링크_공유_생성(self, mock_collection: MagicMock) -> None:
        """SC-DOC-007: 외부 링크 공유를 생성한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "published",
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentShareService("T1")
        expires = datetime.now(tz=UTC) + timedelta(days=30)
        result = svc.create_share(
            document_id="DOC-0001",
            share_type="external_link",
            permission="viewer",
            expires_at=expires,
            password="SecureLink123!",  # noqa: S106
            max_downloads=10,
            shared_by="EMP-001",
        )

        assert result["share_type"] == "external_link"
        assert result["external_link_token"] is not None
        assert result["max_downloads"] == 10

    def test_외부_링크_만료일_필수(self, mock_collection: MagicMock) -> None:
        """BR-DOC-013: 외부 링크 생성 시 만료일 누락 에러 (ERR-DOC-013)."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "tenant_id": "T1",
        }

        svc = DocumentShareService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_share(
                document_id="DOC-0001",
                share_type="external_link",
                shared_by="EMP-001",
            )
        assert exc_info.value.status_code == 400
        assert "ERR-DOC-013" in (exc_info.value.detail or "")

    def test_외부_링크_만료일_초과(self, mock_collection: MagicMock) -> None:
        """외부 링크 만료일이 90일을 초과하면 에러."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "tenant_id": "T1",
        }

        svc = DocumentShareService("T1")
        expires = datetime.now(tz=UTC) + timedelta(days=100)
        with pytest.raises(OneERPError) as exc_info:
            svc.create_share(
                document_id="DOC-0001",
                share_type="external_link",
                expires_at=expires,
                shared_by="EMP-001",
            )
        assert exc_info.value.status_code == 400

    def test_문서_미존재_공유_실패(self, mock_collection: MagicMock) -> None:
        """존재하지 않는 문서 공유 시 404 에러."""
        mock_collection.find_one.return_value = None

        svc = DocumentShareService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_share(
                document_id="DOC-9999",
                share_type="user",
                shared_by="EMP-001",
            )
        assert exc_info.value.status_code == 404

    def test_공유_취소(self, mock_collection: MagicMock) -> None:
        """공유를 비활성화한다."""
        mock_collection.find_one.return_value = {
            "_id": "DS-0001",
            "document_id": "DOC-0001",
            "is_active": True,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = DocumentShareService("T1")
        result = svc.revoke_share("DS-0001", actor="EMP-001")

        assert result["is_active"] is False
