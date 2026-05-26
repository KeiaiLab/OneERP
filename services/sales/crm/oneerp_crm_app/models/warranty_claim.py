"""보증 클레임(WarrantyClaim) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class WarrantyClaimCreate(BaseModel):
    """보증 클레임 생성 요청 스키마."""

    customer_id: str
    item_code: str = ""
    claim_date: date | None = None
    issue_description: str = ""
    serial_no: str = ""
    resolution: str = ""
    is_resolved: bool = False


class WarrantyClaimUpdate(BaseModel):
    """보증 클레임 수정 요청 스키마."""

    customer_id: str | None = None
    item_code: str | None = None
    claim_date: date | None = None
    issue_description: str | None = None
    serial_no: str | None = None
    resolution: str | None = None
    is_resolved: bool | None = None


class WarrantyClaim(BaseDocument):
    """보증 클레임 문서."""

    customer_id: str = ""
    item_code: str = ""
    claim_date: date | None = None
    issue_description: str = ""
    serial_no: str = ""
    resolution: str = ""
    is_resolved: bool = False
