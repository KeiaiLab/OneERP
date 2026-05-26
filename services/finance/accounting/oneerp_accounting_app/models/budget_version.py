"""예산 버전(BudgetVersion) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class BudgetVersionStatus(StrEnum):
    """예산 버전 상태."""

    DRAFT = "draft"
    APPROVED = "approved"
    LOCKED = "locked"


class BudgetVersionCreate(BaseModel):
    """예산 버전 생성 요청 스키마."""

    budget_id: str
    version_no: int = 1
    version_name: str = ""
    total_amount: Decimal = Decimal(0)
    is_current: bool = False


class BudgetVersionUpdate(BaseModel):
    """예산 버전 수정 요청 스키마."""

    budget_id: str | None = None
    version_no: int | None = None
    version_name: str | None = None
    total_amount: Decimal | None = None
    is_current: bool | None = None


class BudgetVersion(BaseDocument):
    """예산 버전 문서."""

    status: BudgetVersionStatus = Field(
        default=BudgetVersionStatus.DRAFT,
        description="예산 버전 상태",
    )
    budget_id: str = ""
    version_no: int = 1
    version_name: str = ""
    total_amount: Decimal = Decimal(0)
    is_current: bool = False
