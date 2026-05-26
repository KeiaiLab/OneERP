"""계약 템플릿(ContractTemplate) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ContractTemplateCreate(BaseModel):
    """계약 템플릿 생성 요청 스키마."""

    template_name: str
    contract_type: str = ""
    template_body: str = ""
    variables: list[str] = []
    approval_required: bool = False


class ContractTemplateUpdate(BaseModel):
    """계약 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    contract_type: str | None = None
    template_body: str | None = None
    variables: list[str] | None = None
    approval_required: bool | None = None


class ContractTemplate(BaseDocument):
    """계약 템플릿 문서."""

    template_name: str = ""
    contract_type: str = ""
    template_body: str = ""
    variables: list[str] = []
    approval_required: bool = False
