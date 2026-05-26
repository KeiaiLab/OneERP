"""구매승인매트릭스(BuyerApprovalMatrix) 설정 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BuyerApprovalMatrixCreate(BaseModel):
    """구매승인매트릭스 생성 요청 스키마."""

    item_group: str
    min_amount: Decimal = Decimal(0)
    max_amount: Decimal = Decimal(0)
    approver: str = ""
    is_active: bool = True


class BuyerApprovalMatrixUpdate(BaseModel):
    """구매승인매트릭스 수정 요청 스키마."""

    item_group: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    approver: str | None = None
    is_active: bool | None = None


class BuyerApprovalMatrix(BaseDocument):
    """구매승인매트릭스 — 품목 그룹별 구매 승인 권한 설정.

    naming prefix: BAM
    """

    item_group: str = ""
    min_amount: Decimal = Decimal(0)
    max_amount: Decimal = Decimal(0)
    approver: str = ""
    is_active: bool = True
