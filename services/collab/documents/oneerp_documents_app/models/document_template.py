"""문서 템플릿(DocumentTemplate) 모델 — 표준 문서 양식 사전 정의.

변수 플레이스홀더({{key}})를 사용한 자동 문서 생성을 지원한다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class TemplateVariable(BaseModel):
    """템플릿 변수 임베디드 모델."""

    key: str = ""
    label: str = ""
    type: str = "string"
    required: bool = False
    default_value: str | None = None
    source: str | None = None
    options: list[str] = Field(default_factory=list)


class DocumentTemplateCreate(BaseModel):
    """문서 템플릿 생성 요청 스키마."""

    template_name: str = Field(min_length=1, max_length=200, description="템플릿명")
    description: str = Field(default="", max_length=2000, description="설명")
    company: str = Field(default="", description="회사 ID")
    category: str | None = Field(default=None, description="기본 분류 ID")
    content_template: str = Field(min_length=1, description="템플릿 내용")
    variables: list[TemplateVariable] = Field(default_factory=list)
    default_security_level: str = Field(default="internal", description="기본 보안 등급")
    default_retention_policy: str | None = Field(default=None)
    default_tags: list[str] = Field(default_factory=list)
    approval_template_id: str | None = Field(default=None)


class DocumentTemplateUpdate(BaseModel):
    """문서 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    description: str | None = None
    category: str | None = None
    content_template: str | None = None
    variables: list[TemplateVariable] | None = None
    default_security_level: str | None = None
    default_retention_policy: str | None = None
    default_tags: list[str] | None = None
    is_active: bool | None = None


class DocumentTemplate(BaseDocument):
    """문서 템플릿 엔티티.

    표준 문서 양식을 사전 정의하며, 변수 바인딩으로 자동 채움을 지원한다.
    """

    company: str = ""
    template_name: str = ""
    description: str = ""
    category: str | None = None
    content_template: str = ""
    variables: list[TemplateVariable] = Field(default_factory=list)
    default_security_level: str = "internal"
    default_retention_policy: str | None = None
    default_tags: list[str] = Field(default_factory=list)
    approval_template_id: str | None = None
    is_active: bool = True
    usage_count: int = 0
    is_deleted: bool = False
