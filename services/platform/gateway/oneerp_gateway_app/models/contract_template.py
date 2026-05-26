"""계약 템플릿(ContractTemplate) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ContractTemplateCreate(BaseModel):
    """계약 템플릿 생성 요청 스키마."""

    template_name: str
    contract_type: str = ""
    template_content: str = ""
    is_active: bool = True


class ContractTemplateUpdate(BaseModel):
    """계약 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    contract_type: str | None = None
    template_content: str | None = None
    is_active: bool | None = None


class ContractTemplate(BaseDocument):
    """계약 템플릿 문서."""

    template_name: str = ""
    contract_type: str = ""
    template_content: str = ""
    is_active: bool = True
