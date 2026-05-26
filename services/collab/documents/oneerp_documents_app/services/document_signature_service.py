"""전자서명 서비스 — 문서 서명/검증/무효화.

BR-DOC-015: 서명 시점 문서 해시 무결성 검증.
BR-DOC-016: 서명 후 편집 금지.
SC-DOC-008: 전자서명 (공동인증서).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


def _compute_document_hash(title: str, content: str, file_checksums: list[str]) -> str:
    """문서 해시를 계산한다."""
    sorted_checksums = sorted(file_checksums)
    canonical = title + "\n" + content + "\n" + "\n".join(sorted_checksums)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class DocumentSignatureService:
    """전자서명 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._sig_repo = Repository("document_signatures", tenant_id=tenant_id)
        self._doc_repo = Repository("documents", tenant_id=tenant_id)
        self._audit_repo = Repository("document_audit_logs", tenant_id=tenant_id)

    def sign_document(
        self,
        *,
        document_id: str,
        signer: str,
        signature_type: str,
        signature_data: str,
        certificate_info: dict[str, object] | None = None,
        certificate_serial: str | None = None,
    ) -> dict[str, Any]:
        """문서에 전자서명을 수행한다 (SC-DOC-008).

        BR-DOC-015: 서명 시점 문서 해시 무결성 검증.
        """
        doc = self._doc_repo.find_by_id(document_id)
        if not doc:
            raise_not_found("요청하신 문서를 찾을 수 없습니다 [ERR-DOC-040]")
        doc = cast("dict[str, Any]", doc)

        # 문서 해시 계산
        file_checksums = [
            f.get("checksum", "") for f in doc.get("file_attachments", []) if f.get("checksum")
        ]
        document_hash = _compute_document_hash(
            doc.get("title", ""),
            doc.get("content", ""),
            file_checksums,
        )

        sig_id = generate_name("SG", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)

        sig: dict[str, Any] = {
            "_id": sig_id,
            "document_id": document_id,
            "document_version": doc.get("version", 1),
            "signer": signer,
            "signature_type": signature_type,
            "signature_data": signature_data,
            "certificate_info": certificate_info or {},
            "certificate_serial": certificate_serial,
            "document_hash": document_hash,
            "timestamp_token": None,
            "signed_at": now,
            "is_valid": True,
            "invalidated_reason": None,
            "invalidated_at": None,
            "invalidated_by": None,
            "tenant_id": self._tenant_id,
            "created_at": now,
            "updated_at": now,
        }

        self._sig_repo.insert(sig)
        self._log_audit(document_id, "sign", actor=signer)

        logger.info("전자서명 완료: %s (서명자: %s)", sig_id, signer)
        return sig

    def verify_signature(self, signature_id: str) -> dict[str, Any]:
        """서명의 유효성을 검증한다."""
        sig = self._sig_repo.find_by_id(signature_id)
        if not sig:
            raise_not_found("전자서명을 찾을 수 없습니다")
        sig = cast("dict[str, Any]", sig)

        if not sig.get("is_valid"):
            return {
                **sig,
                "verification_result": "invalid",
                "reason": sig.get("invalidated_reason"),
            }

        # 문서 해시 비교
        doc = self._doc_repo.find_by_id(sig.get("document_id", ""))
        if not doc:
            return {**sig, "verification_result": "document_missing"}
        doc = cast("dict[str, Any]", doc)

        file_checksums = [
            f.get("checksum", "") for f in doc.get("file_attachments", []) if f.get("checksum")
        ]
        current_hash = _compute_document_hash(
            doc.get("title", ""),
            doc.get("content", ""),
            file_checksums,
        )

        if current_hash != sig.get("document_hash"):
            return {**sig, "verification_result": "hash_mismatch"}

        return {**sig, "verification_result": "valid"}

    def get_signatures_by_document(self, document_id: str) -> list[dict[str, Any]]:
        """문서의 서명 목록을 조회한다."""
        return self._sig_repo.find_many({"document_id": document_id}, limit=100)

    def invalidate_signature(
        self,
        signature_id: str,
        *,
        reason: str,
        actor: str = "",
    ) -> dict[str, Any]:
        """서명을 무효화한다."""
        sig = self._sig_repo.find_by_id(signature_id)
        if not sig:
            raise_not_found("전자서명을 찾을 수 없습니다")
        sig = cast("dict[str, Any]", sig)

        now = datetime.now(tz=UTC)
        self._sig_repo.update_by_id(
            signature_id,
            {
                "is_valid": False,
                "invalidated_reason": reason,
                "invalidated_at": now,
                "invalidated_by": actor,
            },
        )
        logger.info("전자서명 무효화: %s (사유: %s)", signature_id, reason)
        return {
            **sig,
            "is_valid": False,
            "invalidated_reason": reason,
            "invalidated_at": now,
        }

    def _log_audit(self, document_id: str, action: str, *, actor: str = "") -> None:
        """감사 로그를 기록한다."""
        log_id = generate_name("AL", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)
        self._audit_repo.insert(
            {
                "_id": log_id,
                "document_id": document_id,
                "action": action,
                "actor": actor,
                "details": {},
                "timestamp": now,
                "tenant_id": self._tenant_id,
                "created_at": now,
                "updated_at": now,
            }
        )
