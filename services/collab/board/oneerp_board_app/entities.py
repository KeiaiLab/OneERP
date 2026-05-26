"""Board 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

12개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.attachment import Attachment, AttachmentCreate, AttachmentUpdate
from .models.audit_log import AuditLog, AuditLogCreate, AuditLogUpdate
from .models.auto_post_rule import AutoPostRule, AutoPostRuleCreate, AutoPostRuleUpdate
from .models.board import Board, BoardCreate, BoardUpdate
from .models.board_permission import (
    BoardPermission,
    BoardPermissionCreate,
    BoardPermissionUpdate,
)
from .models.comment import Comment, CommentCreate, CommentUpdate
from .models.popup_notice import PopupNotice, PopupNoticeCreate, PopupNoticeUpdate
from .models.post import Post, PostCreate, PostUpdate
from .models.post_bookmark import PostBookmark, PostBookmarkCreate, PostBookmarkUpdate
from .models.post_like import PostLike, PostLikeCreate, PostLikeUpdate
from .models.post_report import PostReport, PostReportCreate, PostReportUpdate
from .models.read_confirmation import (
    ReadConfirmation,
    ReadConfirmationCreate,
    ReadConfirmationUpdate,
)

# --- 마스터 데이터 ---

BOARD = EntityMeta(
    collection="boards",
    prefix="BRD",
    api_path="/api/v1/boards",
    tag="게시판",
    resource="board",
    model=Board,
    create_schema=BoardCreate,
    update_schema=BoardUpdate,
    archetype="master",
    not_found_message="게시판을 찾을 수 없습니다",
)

BOARD_PERMISSION = EntityMeta(
    collection="board_permissions",
    prefix="BPM",
    api_path="/api/v1/board-permissions",
    tag="게시판 권한",
    resource="board_permission",
    model=BoardPermission,
    create_schema=BoardPermissionCreate,
    update_schema=BoardPermissionUpdate,
    archetype="master",
    not_found_message="게시판 권한을 찾을 수 없습니다",
)

AUTO_POST_RULE = EntityMeta(
    collection="auto_post_rules",
    prefix="APR",
    api_path="/api/v1/auto-post-rules",
    tag="자동 공지 규칙",
    resource="auto_post_rule",
    model=AutoPostRule,
    create_schema=AutoPostRuleCreate,
    update_schema=AutoPostRuleUpdate,
    archetype="master",
    not_found_message="자동 공지 규칙을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

POST = EntityMeta(
    collection="posts",
    prefix="PST",
    api_path="/api/v1/posts",
    tag="게시글",
    resource="post",
    model=Post,
    create_schema=PostCreate,
    update_schema=PostUpdate,
    archetype="transaction",
    not_found_message="게시글을 찾을 수 없습니다",
)

COMMENT = EntityMeta(
    collection="comments",
    prefix="CMT",
    api_path="/api/v1/comments",
    tag="댓글",
    resource="comment",
    model=Comment,
    create_schema=CommentCreate,
    update_schema=CommentUpdate,
    archetype="transaction",
    not_found_message="댓글을 찾을 수 없습니다",
)

ATTACHMENT = EntityMeta(
    collection="attachments",
    prefix="ATT",
    api_path="/api/v1/attachments",
    tag="첨부파일",
    resource="attachment",
    model=Attachment,
    create_schema=AttachmentCreate,
    update_schema=AttachmentUpdate,
    archetype="transaction",
    not_found_message="첨부파일을 찾을 수 없습니다",
)

READ_CONFIRMATION = EntityMeta(
    collection="read_confirmations",
    prefix="RC",
    api_path="/api/v1/read-confirmations",
    tag="필독 확인",
    resource="read_confirmation",
    model=ReadConfirmation,
    create_schema=ReadConfirmationCreate,
    update_schema=ReadConfirmationUpdate,
    archetype="transaction",
    not_found_message="필독 확인을 찾을 수 없습니다",
)

POPUP_NOTICE = EntityMeta(
    collection="popup_notices",
    prefix="POP",
    api_path="/api/v1/popup-notices",
    tag="팝업 공지",
    resource="popup_notice",
    model=PopupNotice,
    create_schema=PopupNoticeCreate,
    update_schema=PopupNoticeUpdate,
    archetype="transaction",
    not_found_message="팝업 공지를 찾을 수 없습니다",
)

POST_LIKE = EntityMeta(
    collection="post_likes",
    prefix="LK",
    api_path="/api/v1/post-likes",
    tag="좋아요",
    resource="post_like",
    model=PostLike,
    create_schema=PostLikeCreate,
    update_schema=PostLikeUpdate,
    archetype="transaction",
    not_found_message="좋아요를 찾을 수 없습니다",
)

POST_BOOKMARK = EntityMeta(
    collection="post_bookmarks",
    prefix="BM",
    api_path="/api/v1/post-bookmarks",
    tag="북마크",
    resource="post_bookmark",
    model=PostBookmark,
    create_schema=PostBookmarkCreate,
    update_schema=PostBookmarkUpdate,
    archetype="transaction",
    not_found_message="북마크를 찾을 수 없습니다",
)

POST_REPORT = EntityMeta(
    collection="post_reports",
    prefix="RPT",
    api_path="/api/v1/post-reports",
    tag="게시글 신고",
    resource="post_report",
    model=PostReport,
    create_schema=PostReportCreate,
    update_schema=PostReportUpdate,
    archetype="transaction",
    not_found_message="게시글 신고를 찾을 수 없습니다",
)

AUDIT_LOG = EntityMeta(
    collection="audit_logs",
    prefix="AL",
    api_path="/api/v1/audit-logs",
    tag="감사 로그",
    resource="audit_log",
    model=AuditLog,
    create_schema=AuditLogCreate,
    update_schema=AuditLogUpdate,
    archetype="transaction",
    not_found_message="감사 로그를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    BOARD,
    BOARD_PERMISSION,
    AUTO_POST_RULE,
    # 트랜잭션
    POST,
    COMMENT,
    ATTACHMENT,
    READ_CONFIRMATION,
    POPUP_NOTICE,
    POST_LIKE,
    POST_BOOKMARK,
    POST_REPORT,
    AUDIT_LOG,
]
