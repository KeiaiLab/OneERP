"""전자서명 서비스 단위 테스트.

SC-DOC-008: 전자서명.
BR-DOC-015: 서명 시점 문서 해시 무결성 검증.
BR-DOC-016: 서명 후 편집 금지.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_documents_app.services.document_signature_service import (
    DocumentSignatureService,
    _compute_document_hash,
)


class TestDocumentSignatureService:
    """DocumentSignatureService 테스트."""

    def test_전자서명_생성(self, mock_collection: MagicMock) -> None:
        """SC-DOC-008: 문서에 전자서명을 수행한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "title": "계약서",
            "content": "계약 내용",
            "version": 3,
            "file_attachments": [],
            "tenant_id": "T1",
        }
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentSignatureService("T1")
        result = svc.sign_document(
            document_id="DOC-0001",
            signer="EMP-003",
            signature_type="joint_certificate",
            signature_data="base64-encoded-data",
            certificate_info={"issuer": "한국정보인증"},
        )

        assert result["document_id"] == "DOC-0001"
        assert result["signer"] == "EMP-003"
        assert result["is_valid"] is True
        assert result["document_hash"] != ""

    def test_서명_검증_성공(self, mock_collection: MagicMock) -> None:
        """서명 유효성 검증 — 해시 일치 시 valid."""
        doc_hash = _compute_document_hash("제목", "내용", [])
        mock_collection.find_one.side_effect = [
            # 서명 조회
            {
                "_id": "SG-0001",
                "document_id": "DOC-0001",
                "is_valid": True,
                "document_hash": doc_hash,
            },
            # 문서 조회
            {
                "_id": "DOC-0001",
                "title": "제목",
                "content": "내용",
                "file_attachments": [],
            },
        ]

        svc = DocumentSignatureService("T1")
        result = svc.verify_signature("SG-0001")

        assert result["verification_result"] == "valid"

    def test_서명_검증_해시_불일치(self, mock_collection: MagicMock) -> None:
        """서명 검증 — 문서 변경 시 hash_mismatch."""
        mock_collection.find_one.side_effect = [
            # 서명 조회
            {
                "_id": "SG-0001",
                "document_id": "DOC-0001",
                "is_valid": True,
                "document_hash": "old-hash",
            },
            # 문서 조회 (변경됨)
            {
                "_id": "DOC-0001",
                "title": "변경된 제목",
                "content": "변경된 내용",
                "file_attachments": [],
            },
        ]

        svc = DocumentSignatureService("T1")
        result = svc.verify_signature("SG-0001")

        assert result["verification_result"] == "hash_mismatch"

    def test_서명_무효화(self, mock_collection: MagicMock) -> None:
        """서명을 무효화한다."""
        mock_collection.find_one.return_value = {
            "_id": "SG-0001",
            "is_valid": True,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = DocumentSignatureService("T1")
        result = svc.invalidate_signature("SG-0001", reason="인증서 만료", actor="admin")

        assert result["is_valid"] is False
        assert result["invalidated_reason"] == "인증서 만료"

    def test_문서_미존재_서명_실패(self, mock_collection: MagicMock) -> None:
        """존재하지 않는 문서 서명 시 404 에러."""
        mock_collection.find_one.return_value = None

        svc = DocumentSignatureService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.sign_document(
                document_id="DOC-9999",
                signer="EMP-001",
                signature_type="joint_certificate",
                signature_data="data",
            )
        assert exc_info.value.status_code == 404
