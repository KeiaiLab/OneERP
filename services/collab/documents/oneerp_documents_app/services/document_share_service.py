"""문서 공유 서비스 — 내부/외부 공유 관리.

BR-DOC-013: 외부 공유 링크 만료일 필수, 최대 90일.
SC-DOC-007: 외부 링크 생성.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_MAX_EXTERNAL_LINK_DAYS = 90


class DocumentShareService:
    """문서 공유 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._share_repo = Repository("document_shares", tenant_id=tenant_id)
        self._doc_repo = Repository("documents", tenant_id=tenant_id)
        self._audit_repo = Repository("document_audit_logs", tenant_id=tenant_id)

    def create_share(
        self,
        *,
        document_id: str,
        share_type: str,
        target_user: str | None = None,
        target_department: str | None = None,
        permission: str = "viewer",
        expires_at: datetime | None = None,
        password: str | None = None,
        max_downloads: int | None = None,
        shared_by: str = "",
    ) -> dict[str, Any]:
        """문서 공유를 생성한다 (SC-DOC-007).

        BR-DOC-013: external_link 타입 시 만료일 필수.
        """
        # 문서 존재 확인
        doc = self._doc_repo.find_by_id(document_id)
        if not doc:
            raise_not_found("요청하신 문서를 찾을 수 없습니다 [ERR-DOC-040]")

        # BR-DOC-013: 외부 링크 만료일 필수
        if share_type == "external_link":
            if not expires_at:
                raise_bad_request("외부 공유 링크에는 만료일 설정이 필수입니다 [ERR-DOC-013]")
            validated_expires_at = cast("datetime", expires_at)
            now = datetime.now(tz=UTC)
            max_expiry = now + timedelta(days=_MAX_EXTERNAL_LINK_DAYS)
            if validated_expires_at > max_expiry:
                raise_bad_request(f"외부 링크 만료일은 최대 {_MAX_EXTERNAL_LINK_DAYS}일입니다")

        share_id = generate_name("DS", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)

        share: dict[str, Any] = {
            "_id": share_id,
            "document_id": document_id,
            "share_type": share_type,
            "target_user": target_user,
            "target_department": target_department,
            "permission": permission,
            "external_link_token": str(uuid4()) if share_type == "external_link" else None,
            "external_link_password": password,
            "expires_at": expires_at,
            "max_downloads": max_downloads,
            "download_count": 0,
            "is_active": True,
            "shared_by": shared_by,
            "tenant_id": self._tenant_id,
            "created_at": now,
            "updated_at": now,
        }

        self._share_repo.insert(share)
        self._log_audit(document_id, "share", actor=shared_by)

        logger.info("문서 공유 생성: %s (유형: %s)", share_id, share_type)
        return share

    def get_shares_by_document(self, document_id: str) -> list[dict[str, Any]]:
        """문서의 공유 목록을 조회한다."""
        return self._share_repo.find_many(
            {"document_id": document_id, "is_active": True}, limit=100
        )

    def revoke_share(self, share_id: str, *, actor: str = "") -> dict[str, Any]:
        """공유를 취소한다."""
        share = self._share_repo.find_by_id(share_id)
        if not share:
            raise_not_found("문서 공유를 찾을 수 없습니다")
        share = cast("dict[str, Any]", share)

        self._share_repo.update_by_id(share_id, {"is_active": False})
        document_id = share.get("document_id", "")
        if document_id:
            self._log_audit(document_id, "share", actor=actor)
        logger.info("문서 공유 취소: %s", share_id)
        return {**share, "is_active": False}

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
