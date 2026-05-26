"""사내 메일 템플릿(MailTemplate) 문서 모델.

BR-MAIL-020: 템플릿명은 테넌트 내에서 고유해야 한다.
BR-MAIL-021: 템플릿 변수는 {{변수명}} 형식으로 정의한다.
"""

from __future__ import annotations

from typing import Annotated

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class MailTemplateCreate(BaseModel):
    """메일 템플릿 생성 요청 스키마."""

    template_name: Annotated[str, Field(min_length=1, max_length=200)]
    subject_template: str = ""
    body_template: str = ""
    body_html_template: str = ""
    category: str = ""
    variables: list[str] = []
    is_active: bool = True
    description: str = ""


class MailTemplateUpdate(BaseModel):
    """메일 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    subject_template: str | None = None
    body_template: str | None = None
    body_html_template: str | None = None
    category: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None
    description: str | None = None


class MailTemplate(BaseDocument):
    """사내 메일 템플릿 문서.

    BR-MAIL-020 ~ BR-MAIL-021 비즈니스 규칙을 적용한다.
    """

    template_name: str = ""
    subject_template: str = ""
    body_template: str = ""
    body_html_template: str = ""
    category: str = ""
    variables: list[str] = []
    is_active: bool = True
    description: str = ""
    usage_count: int = 0
