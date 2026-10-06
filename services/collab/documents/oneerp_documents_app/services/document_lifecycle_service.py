"""문서 생명주기 서비스 — 상태 전이, 버전 관리, 감사 로그.

SC-DOC-001~005: 문서 생성, 수정, 제출, 승인, 배포.
BR-DOC-001~017: 문서 관련 비즈니스 룰.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import UTC, datetime
from typing import Any, cast

from dateutil.relativedelta import relativedelta
from oneerp_core.errors import (
    raise_bad_request,
    raise_conflict,
    raise_not_found,
    raise_unprocessable,
)
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 상태 전이 규칙: 현재 상태 → 허용되는 다음 상태 목록
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["review", "published"],
    "review": ["approved", "draft"],
    "approved": ["published", "archived"],
    "published": ["draft", "archived", "disposed"],
    "archived": ["published", "disposed"],
    "disposed": [],
}

_MAX_TAGS = 30
_MAX_CATEGORY_DEPTH = 10


def _strip_html(html: str) -> str:
    """HTML 태그를 제거하여 플레인텍스트로 변환한다."""
    # 태그 본문에서 '<' 를 배제해 '<<<…' 입력의 O(n²) 역추적을 막는다.
    return re.sub(r"<[^<>]+>", "", html).strip()


def _compute_document_hash(title: str, content: str, file_checksums: list[str]) -> str:
    """문서 해시를 계산한다 (전자서명 무결성 검증용).

    canonical_content = title + '\\n' + content + '\\n' + sorted(file_checksums).join('\\n')
    """
    sorted_checksums = sorted(file_checksums)
    canonical = title + "\n" + content + "\n" + "\n".join(sorted_checksums)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _compute_content_hash(title: str, content: str) -> str:
    """콘텐츠 해시를 계산한다 (버전 스냅샷용)."""
    return hashlib.sha256((title + "\n" + content).encode("utf-8")).hexdigest()


class DocumentLifecycleService:
    """문서 생명주기 관리 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._doc_repo = Repository("documents", tenant_id=tenant_id)
        self._ver_repo = Repository("document_versions", tenant_id=tenant_id)
        self._audit_repo = Repository("document_audit_logs", tenant_id=tenant_id)
        self._sig_repo = Repository("document_signatures", tenant_id=tenant_id)
        self._cat_repo = Repository("document_categories", tenant_id=tenant_id)
        self._rp_repo = Repository("retention_policies", tenant_id=tenant_id)
        self._tpl_repo = Repository("document_templates", tenant_id=tenant_id)

    # ──────────────────────────────────────────────
    # 문서 생성
    # ──────────────────────────────────────────────

    def create_document(
        self,
        *,
        title: str,
        category: str,
        content: str = "",
        template_id: str | None = None,
        template_variables: dict[str, str] | None = None,
        security_level: str = "internal",
        tags: list[str] | None = None,
        metadata: dict[str, object] | None = None,
        department: str = "",
        company: str = "",
        summary: str = "",
        author: str = "",
    ) -> dict[str, Any]:
        """문서를 생성한다 (SC-DOC-001).

        BR-DOC-001: 문서번호 자동 부여.
        BR-DOC-002: 카테고리 필수 지정.
        BR-DOC-004: 보안 등급 상속.
        """
        if tags and len(tags) > _MAX_TAGS:
            raise_bad_request(f"태그는 최대 {_MAX_TAGS}개까지 허용됩니다")

        # 템플릿 바인딩
        if template_id:
            content = self._apply_template(template_id, template_variables or {}, content)

        content_plain = _strip_html(content) if content else ""

        doc_id = generate_name("DOC", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)

        doc: dict[str, Any] = {
            "_id": doc_id,
            "doc_no": doc_id,
            "title": title,
            "category": category,
            "content": content,
            "content_plain": content_plain,
            "summary": summary,
            "file_attachments": [],
            "author": author,
            "department": department,
            "company": company,
            "version": 1,
            "status": "draft",
            "security_level": security_level,
            "retention_policy": None,
            "retention_until": None,
            "tags": tags or [],
            "metadata": metadata or {},
            "template_id": template_id,
            "is_locked": False,
            "locked_by": None,
            "locked_at": None,
            "download_restricted": False,
            "watermark_enabled": False,
            "is_deleted": False,
            "tenant_id": self._tenant_id,
            "created_at": now,
            "updated_at": now,
            "created_by": author,
            "updated_by": author,
        }

        self._doc_repo.insert(doc)

        # 초기 버전 생성
        self._create_version(
            document_id=doc_id,
            version_no=1,
            version_type="minor",
            title=title,
            content=content,
            change_summary="초기 생성",
            changed_by=author,
        )

        # 감사 로그
        self._log_audit(doc_id, "create", actor=author)

        logger.info("문서 생성: %s (제목: %s)", doc_id, title)
        return doc

    # ──────────────────────────────────────────────
    # 문서 수정
    # ──────────────────────────────────────────────

    def update_document(
        self,
        document_id: str,
        *,
        actor: str = "",
        **updates: Any,
    ) -> dict[str, Any]:
        """문서를 수정한다 (SC-DOC-002).

        BR-DOC-006: 버전 자동 생성.
        BR-DOC-008: 체크아웃 잠금 확인.
        BR-DOC-016: 서명 후 편집 금지.
        """
        doc = self._get_doc_or_404(document_id)

        # BR-DOC-016: 서명 후 편집 금지
        self._check_signed(document_id)

        # BR-DOC-008: 체크아웃 잠금 확인
        self._check_lock(doc, actor)

        change_summary = updates.pop("change_summary", "")
        update_fields: dict[str, Any] = {}
        content_changed = False

        for key, val in updates.items():
            if val is not None:
                update_fields[key] = val
                if key in ("title", "content"):
                    content_changed = True

        if "content" in update_fields:
            update_fields["content_plain"] = _strip_html(update_fields["content"])

        if "tags" in update_fields and len(update_fields["tags"]) > _MAX_TAGS:
            raise_bad_request(f"태그는 최대 {_MAX_TAGS}개까지 허용됩니다")

        now = datetime.now(tz=UTC)
        update_fields["updated_at"] = now
        update_fields["updated_by"] = actor

        # BR-DOC-006: 콘텐츠 변경 시 버전 자동 생성
        if content_changed:
            new_version = doc.get("version", 1) + 1
            update_fields["version"] = new_version
            self._create_version(
                document_id=document_id,
                version_no=new_version,
                version_type="minor",
                title=update_fields.get("title", doc.get("title", "")),
                content=update_fields.get("content", doc.get("content", "")),
                change_summary=change_summary,
                changed_by=actor,
            )

        self._doc_repo.update_by_id(document_id, update_fields)
        self._log_audit(document_id, "update", actor=actor)

        logger.info("문서 수정: %s", document_id)
        return {**doc, **update_fields}

    # ──────────────────────────────────────────────
    # 상태 전이
    # ──────────────────────────────────────────────

    def submit_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 제출한다 (SC-DOC-003: draft → review)."""
        doc = self._get_doc_or_404(document_id)
        self._validate_transition(doc, "review")

        # 제출 전 필수값 확인
        if not doc.get("title"):
            raise_bad_request("제목은 필수 입력 항목입니다 [ERR-DOC-001]")

        self._doc_repo.update_by_id(
            document_id, {"status": "review", "updated_at": datetime.now(tz=UTC)}
        )
        self._log_audit(document_id, "submit", actor=actor)
        logger.info("문서 제출: %s", document_id)
        return {**doc, "status": "review"}

    def approve_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 승인한다 (SC-DOC-004: review → approved)."""
        doc = self._get_doc_or_404(document_id)
        self._validate_transition(doc, "approved")

        self._doc_repo.update_by_id(
            document_id, {"status": "approved", "updated_at": datetime.now(tz=UTC)}
        )
        self._log_audit(document_id, "approve", actor=actor)
        logger.info("문서 승인: %s", document_id)
        return {**doc, "status": "approved"}

    def reject_document(
        self, document_id: str, *, actor: str = "", reason: str = ""
    ) -> dict[str, Any]:
        """문서를 반려한다 (review → draft)."""
        doc = self._get_doc_or_404(document_id)
        self._validate_transition(doc, "draft")

        self._doc_repo.update_by_id(
            document_id, {"status": "draft", "updated_at": datetime.now(tz=UTC)}
        )
        self._log_audit(document_id, "reject", actor=actor, details={"reason": reason})
        logger.info("문서 반려: %s (사유: %s)", document_id, reason)
        return {**doc, "status": "draft"}

    def publish_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 배포한다 (SC-DOC-005: approved/draft → published).

        BR-DOC-003: 보존 정책 자동 적용.
        BR-DOC-007: 주 버전(major) 자동 생성.
        """
        doc = self._get_doc_or_404(document_id)
        self._validate_transition(doc, "published")

        now = datetime.now(tz=UTC)
        update_fields: dict[str, Any] = {
            "status": "published",
            "updated_at": now,
        }

        # BR-DOC-003: 보존 정책 자동 적용
        retention_until = self._apply_retention_policy(doc, now)
        if retention_until:
            update_fields["retention_until"] = retention_until
            update_fields["retention_policy"] = doc.get(
                "retention_policy"
            ) or self._get_category_retention(doc.get("category", ""))

        # BR-DOC-007: 주 버전 생성
        new_version = doc.get("version", 1) + 1
        update_fields["version"] = new_version
        self._create_version(
            document_id=document_id,
            version_no=new_version,
            version_type="major",
            title=doc.get("title", ""),
            content=doc.get("content", ""),
            change_summary="문서 배포",
            changed_by=actor,
        )

        self._doc_repo.update_by_id(document_id, update_fields)
        self._log_audit(document_id, "publish", actor=actor)
        logger.info("문서 배포: %s", document_id)
        return {**doc, **update_fields}

    def archive_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 아카이브한다 (published/approved → archived)."""
        doc = self._get_doc_or_404(document_id)
        self._validate_transition(doc, "archived")

        self._doc_repo.update_by_id(
            document_id, {"status": "archived", "updated_at": datetime.now(tz=UTC)}
        )
        self._log_audit(document_id, "archive", actor=actor)
        logger.info("문서 아카이브: %s", document_id)
        return {**doc, "status": "archived"}

    def restore_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """아카이브된 문서를 복원한다 (archived → published)."""
        doc = self._get_doc_or_404(document_id)
        self._validate_transition(doc, "published")

        self._doc_repo.update_by_id(
            document_id, {"status": "published", "updated_at": datetime.now(tz=UTC)}
        )
        self._log_audit(document_id, "restore_version", actor=actor)
        logger.info("문서 복원: %s", document_id)
        return {**doc, "status": "published"}

    def dispose_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 폐기한다 (published/archived → disposed)."""
        doc = self._get_doc_or_404(document_id)
        self._validate_transition(doc, "disposed")

        self._doc_repo.update_by_id(
            document_id, {"status": "disposed", "updated_at": datetime.now(tz=UTC)}
        )
        self._log_audit(document_id, "dispose", actor=actor)
        logger.info("문서 폐기: %s", document_id)
        return {**doc, "status": "disposed"}

    # ──────────────────────────────────────────────
    # 소프트 삭제
    # ──────────────────────────────────────────────

    def soft_delete_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 소프트 삭제한다 (BR-DOC-010, BR-DOC-011)."""
        doc = self._get_doc_or_404(document_id)

        # BR-DOC-011: 보존 기간 내 삭제 금지
        retention_until = doc.get("retention_until")
        if retention_until and retention_until > datetime.now(tz=UTC):
            raise_unprocessable(
                "ERR-DOC-011",
                f"보존 기간({retention_until.strftime('%Y-%m-%d')}까지) 내에는 삭제할 수 없습니다",
            )

        now = datetime.now(tz=UTC)
        self._doc_repo.update_by_id(
            document_id,
            {"is_deleted": True, "deleted_at": now, "deleted_by": actor},
        )
        self._log_audit(document_id, "delete", actor=actor)
        logger.info("문서 소프트 삭제: %s", document_id)
        return {**doc, "is_deleted": True, "deleted_at": now}

    # ──────────────────────────────────────────────
    # 체크아웃/체크인
    # ──────────────────────────────────────────────

    def checkout_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 체크아웃한다 (BR-DOC-008)."""
        doc = self._get_doc_or_404(document_id)

        if doc.get("is_locked"):
            locked_by = doc.get("locked_by", "알 수 없음")
            raise_conflict(f"다른 사용자({locked_by})가 편집 중입니다 [ERR-DOC-008]")

        now = datetime.now(tz=UTC)
        self._doc_repo.update_by_id(
            document_id,
            {"is_locked": True, "locked_by": actor, "locked_at": now},
        )
        self._log_audit(document_id, "checkout", actor=actor)
        logger.info("문서 체크아웃: %s (사용자: %s)", document_id, actor)
        return {**doc, "is_locked": True, "locked_by": actor, "locked_at": now}

    def checkin_document(self, document_id: str, *, actor: str = "") -> dict[str, Any]:
        """문서를 체크인한다."""
        doc = self._get_doc_or_404(document_id)

        self._doc_repo.update_by_id(
            document_id,
            {"is_locked": False, "locked_by": None, "locked_at": None},
        )
        self._log_audit(document_id, "checkin", actor=actor)
        logger.info("문서 체크인: %s", document_id)
        return {**doc, "is_locked": False, "locked_by": None, "locked_at": None}

    # ──────────────────────────────────────────────
    # 버전 복원
    # ──────────────────────────────────────────────

    def restore_version(
        self, document_id: str, version_no: int, *, actor: str = ""
    ) -> dict[str, Any]:
        """특정 버전에서 문서를 복원한다 (SC-DOC-010)."""
        doc = self._get_doc_or_404(document_id)

        # 대상 버전 조회
        versions = self._ver_repo.find_many(
            {"document_id": document_id, "version_no": version_no}, limit=1
        )
        if not versions:
            raise_not_found(f"버전 {version_no}을(를) 찾을 수 없습니다")

        target_ver = versions[0]
        new_version = doc.get("version", 1) + 1

        update_fields: dict[str, Any] = {
            "title": target_ver.get("title", ""),
            "content": target_ver.get("content", ""),
            "content_plain": _strip_html(target_ver.get("content", "")),
            "file_attachments": target_ver.get("file_attachments", []),
            "version": new_version,
            "updated_at": datetime.now(tz=UTC),
            "updated_by": actor,
        }

        self._doc_repo.update_by_id(document_id, update_fields)

        # 복원 버전 생성
        self._create_version(
            document_id=document_id,
            version_no=new_version,
            version_type="minor",
            title=target_ver.get("title", ""),
            content=target_ver.get("content", ""),
            change_summary=f"버전 {version_no}에서 복원",
            changed_by=actor,
        )

        self._log_audit(
            document_id,
            "restore_version",
            actor=actor,
            details={"restored_from": version_no},
        )
        logger.info("버전 복원: %s → v%d에서 복원", document_id, version_no)
        return {**doc, **update_fields}

    # ──────────────────────────────────────────────
    # 내부 헬퍼
    # ──────────────────────────────────────────────

    def _get_doc_or_404(self, document_id: str) -> dict[str, Any]:
        """문서를 조회하고 없으면 404를 발생시킨다."""
        doc = self._doc_repo.find_by_id(document_id)
        if doc is None:
            raise_not_found("요청하신 문서를 찾을 수 없습니다 [ERR-DOC-040]")
        return cast("dict[str, Any]", doc)

    def _validate_transition(self, doc: dict[str, Any], target: str) -> None:
        """상태 전이 유효성을 검증한다."""
        current = doc.get("status", "draft")
        allowed = _VALID_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise_unprocessable(
                "ERR-DOC-030",
                f"현재 상태({current})에서 {target}(으)로 전이할 수 없습니다",
            )

    def _check_signed(self, document_id: str) -> None:
        """BR-DOC-016: 유효한 전자서명이 존재하면 편집을 금지한다."""
        sigs = self._sig_repo.find_many({"document_id": document_id, "is_valid": True}, limit=1)
        if sigs:
            raise_conflict("전자서명이 완료된 문서는 수정할 수 없습니다 [ERR-DOC-016]")

    def _check_lock(self, doc: dict[str, Any], actor: str) -> None:
        """BR-DOC-008: 다른 사용자가 잠금 중이면 편집을 금지한다."""
        if doc.get("is_locked") and doc.get("locked_by") != actor:
            locked_by = doc.get("locked_by", "알 수 없음")
            raise_conflict(f"다른 사용자({locked_by})가 편집 중입니다 [ERR-DOC-008]")

    def _create_version(
        self,
        *,
        document_id: str,
        version_no: int,
        version_type: str,
        title: str,
        content: str,
        change_summary: str,
        changed_by: str,
    ) -> dict[str, Any]:
        """문서 버전 스냅샷을 생성한다."""
        ver_id = generate_name("DV", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)
        content_hash = _compute_content_hash(title, content)

        ver: dict[str, Any] = {
            "_id": ver_id,
            "document_id": document_id,
            "version_no": version_no,
            "version_type": version_type,
            "title": title,
            "content": content,
            "file_attachments": [],
            "change_summary": change_summary,
            "changed_by": changed_by,
            "content_hash": content_hash,
            "metadata_snapshot": {},
            "tenant_id": self._tenant_id,
            "created_at": now,
            "updated_at": now,
        }
        self._ver_repo.insert(ver)
        return ver

    def _log_audit(
        self,
        document_id: str,
        action: str,
        *,
        actor: str = "",
        details: dict[str, object] | None = None,
    ) -> None:
        """감사 로그를 기록한다 (BR-DOC-014)."""
        log_id = generate_name("AL", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)
        self._audit_repo.insert(
            {
                "_id": log_id,
                "document_id": document_id,
                "action": action,
                "actor": actor,
                "details": details or {},
                "timestamp": now,
                "tenant_id": self._tenant_id,
                "created_at": now,
                "updated_at": now,
            }
        )

    def _apply_template(
        self,
        template_id: str,
        variables: dict[str, str],
        fallback_content: str,
    ) -> str:
        """템플릿 변수를 바인딩하여 내용을 생성한다."""
        tpl = self._tpl_repo.find_by_id(template_id)
        if not tpl:
            return fallback_content

        content = tpl.get("content_template", fallback_content)
        for key, val in variables.items():
            content = content.replace("{{" + key + "}}", val)
        return content

    def _apply_retention_policy(
        self, doc: dict[str, Any], published_date: datetime
    ) -> datetime | None:
        """보존 정책을 적용하여 만료일을 계산한다 (BR-DOC-003)."""
        policy_id = doc.get("retention_policy") or self._get_category_retention(
            doc.get("category", "")
        )
        if not policy_id:
            return None

        policy = self._rp_repo.find_by_id(policy_id)
        if not policy:
            return None

        years = policy.get("retention_years", 0)
        months = policy.get("retention_months", 0)
        return published_date + relativedelta(years=years, months=months)

    def _get_category_retention(self, category_id: str) -> str | None:
        """카테고리의 기본 보존 정책 ID를 조회한다."""
        if not category_id:
            return None
        cat = self._cat_repo.find_by_id(category_id)
        if not cat:
            return None
        return cat.get("default_retention_policy")
