"""프로젝트 청구(ProjectBilling) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ProjectBillingCreate(BaseModel):
    """프로젝트 청구 생성 요청 스키마."""

    project_id: str
    billing_date: date | None = None
    amount: Decimal = Decimal(0)
    billing_type: str = ""
    is_invoiced: bool = False


class ProjectBillingUpdate(BaseModel):
    """프로젝트 청구 수정 요청 스키마."""

    project_id: str | None = None
    billing_date: date | None = None
    amount: Decimal | None = None
    billing_type: str | None = None
    is_invoiced: bool | None = None


class ProjectBilling(BaseDocument):
    """프로젝트 청구 문서."""

    project_id: str = ""
    billing_date: date | None = None
    amount: Decimal = Decimal(0)
    billing_type: str = ""
    is_invoiced: bool = False
