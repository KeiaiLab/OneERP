"""이메일 템플릿 모델 — 마케팅 이메일 템플릿을 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class EmailTemplateCreate(BaseModel):
    """이메일 템플릿 생성 요청 스키마."""

    template_name: str
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    sender_name: str = ""
    sender_email: str = ""
    reply_to: str = ""
    category: str = ""  # promotional/transactional/newsletter
    variables: list[str] = []  # 치환 가능 변수 목록


class EmailTemplateUpdate(BaseModel):
    """이메일 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    sender_name: str | None = None
    sender_email: str | None = None
    category: str | None = None
    is_active: bool | None = None


class EmailTemplate(BaseDocument):
    """이메일 템플릿 문서 — 마케팅 이메일 템플릿 정보를 저장한다."""

    template_name: str = ""
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    sender_name: str = ""
    sender_email: str = ""
    reply_to: str = ""
    category: str = ""
    variables: list[str] = []
    is_active: bool = True
    usage_count: int = 0
