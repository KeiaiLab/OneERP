"""자동 공지 게시 규칙(AutoPostRule) 문서 모델.

엔티티 정의: L2-spec 1.10
- BR-BRD-015: 자동 공지 게시 규칙 실행
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

from .post import MustReadTarget  # noqa: TC001 — Pydantic 런타임에 필요


class AutoPostRuleCreate(BaseModel):
    """자동 공지 규칙 생성 요청 스키마."""

    rule_name: str
    source_event: str
    source_document_type: str | None = None
    target_board_id: str
    title_template: str
    content_template: str
    is_must_read: bool = False
    must_read_target: MustReadTarget | None = None
    is_active: bool = True


class AutoPostRuleUpdate(BaseModel):
    """자동 공지 규칙 수정 요청 스키마."""

    rule_name: str | None = None
    source_event: str | None = None
    source_document_type: str | None = None
    target_board_id: str | None = None
    title_template: str | None = None
    content_template: str | None = None
    is_must_read: bool | None = None
    must_read_target: MustReadTarget | None = None
    is_active: bool | None = None


class AutoPostRule(BaseDocument):
    """자동 공지 게시 규칙 문서.

    BR-BRD-015: 매칭되는 이벤트 수신 시 title_template/content_template을
    이벤트 데이터로 렌더링하여 자동 게시글 생성.
    """

    rule_name: str = ""
    source_event: str = ""
    source_document_type: str | None = None
    target_board_id: str = ""
    title_template: str = ""
    content_template: str = ""
    is_must_read: bool = False
    must_read_target: MustReadTarget | None = None
    is_active: bool = True
