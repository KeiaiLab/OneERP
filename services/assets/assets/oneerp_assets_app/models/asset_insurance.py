"""자산 보험(AssetInsurance) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetInsuranceCreate(BaseModel):
    """자산 보험 생성 요청 스키마."""

    asset_id: str
    insurer: str = ""
    policy_number: str = ""
    coverage_amount: Decimal = Decimal(0)
    premium: Decimal = Decimal(0)
    start_date: date | None = None
    end_date: date | None = None


class AssetInsuranceUpdate(BaseModel):
    """자산 보험 수정 요청 스키마."""

    asset_id: str | None = None
    insurer: str | None = None
    policy_number: str | None = None
    coverage_amount: Decimal | None = None
    premium: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None


class AssetInsurance(BaseDocument):
    """자산 보험 문서."""

    asset_id: str = ""
    insurer: str = ""
    policy_number: str = ""
    coverage_amount: Decimal = Decimal(0)
    premium: Decimal = Decimal(0)
    start_date: date | None = None
    end_date: date | None = None
