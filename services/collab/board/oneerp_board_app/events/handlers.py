"""Board 서비스 이벤트 핸들러 — 구독 이벤트 처리.

L2-spec 6.2 구독 이벤트:
- APPROVAL_REQUEST_APPROVED: AutoPostRule 매칭 → 자동 공지 게시 (BR-BRD-015)
- ORGANIZATION_CHANGED: 게시판 권한 자동 동기화
- EMPLOYEE_DEACTIVATED: 퇴직 직원 필독/권한 정리
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


def handle_approval_approved(event_data: dict[str, Any]) -> None:
    """결재 완료 이벤트를 수신하여 자동 공지를 게시한다.

    BR-BRD-015: AutoPostRule에 매칭되는 이벤트를 수신하면
    템플릿을 렌더링하여 자동 게시글 생성.
    """
    tenant_id = event_data.get("tenant_id", "")
    document_type = event_data.get("document_type", "")
    document_data = event_data.get("document_data", {})

    rule_repo = Repository("auto_post_rules", tenant_id=tenant_id)

    # 매칭되는 규칙 조회
    query: dict[str, Any] = {
        "source_event": "APPROVAL_REQUEST_APPROVED",
        "is_active": True,
    }
    rules = rule_repo.find_many(query, limit=50)

    post_repo = Repository("posts", tenant_id=tenant_id)

    for rule in rules:
        # source_document_type 필터 (null이면 전체 매칭)
        rule_doc_type = rule.get("source_document_type")
        if rule_doc_type and rule_doc_type != document_type:
            continue

        # 템플릿 렌더링 (간단한 format 기반)
        title_template = rule.get("title_template", "")
        content_template = rule.get("content_template", "")

        try:
            title = title_template.format(**document_data)
            content = content_template.format(**document_data)
        except Exception:
            logger.warning(
                "자동 공지 템플릿 렌더링 실패: %s",
                rule.get("_id", ""),
            )
            continue

        post_id = generate_name("PST", tenant_id=tenant_id)
        post_repo.insert(
            {
                "_id": post_id,
                "board_id": rule.get("target_board_id", ""),
                "title": title,
                "content": content,
                "content_plain": content,
                "status": "published",
                "source_type": "approval_auto",
                "source_ref": event_data.get("document_id", ""),
                "is_must_read": rule.get("is_must_read", False),
                "must_read_target": rule.get("must_read_target"),
                "author_id": "system",
                "author_name": "시스템",
                "tenant_id": tenant_id,
            }
        )

        logger.info(
            "자동 공지 게시: %s (규칙: %s, 문서: %s)",
            post_id,
            rule.get("_id", ""),
            document_type,
        )


def handle_employee_deactivated(event_data: dict[str, Any]) -> None:
    """퇴직 직원의 필독 레코드/권한을 정리한다.

    L2-spec 6.2: EMPLOYEE_DEACTIVATED 이벤트 처리.
    """
    tenant_id = event_data.get("tenant_id", "")
    user_id = event_data.get("user_id", "")

    if not user_id:
        return

    # 미확인 필독 레코드 정리
    rc_repo = Repository("read_confirmations", tenant_id=tenant_id)
    unread = rc_repo.find_many(
        {"user_id": user_id, "status": {"$ne": "read"}},
        limit=500,
    )
    for rc in unread:
        rc_repo.update_by_id(rc.get("_id", ""), {"status": "read", "read_at": "deactivated"})

    # 개인 권한 비활성화
    perm_repo = Repository("board_permissions", tenant_id=tenant_id)
    perms = perm_repo.find_many(
        {"grantee_type": "user", "grantee_id": user_id, "is_active": True},
        limit=100,
    )
    for perm in perms:
        perm_repo.update_by_id(perm.get("_id", ""), {"is_active": False})

    logger.info("퇴직 직원 정리: %s (RC: %d건, 권한: %d건)", user_id, len(unread), len(perms))
