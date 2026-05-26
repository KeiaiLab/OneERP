"""위험물 관리(HazardousMaterial) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from decimal import Decimal


class HazardousMaterialCreate(BaseModel):
    """위험물 생성 요청 스키마."""

    material_name: str
    cas_number: str | None = None
    item: str | None = None
    ghs_classification: list[str]
    msds_document: str
    storage_conditions: str
    max_storage_qty: Decimal | None = None
    current_qty: Decimal | None = None
    emergency_contact: str
    regulatory_status: str | None = None


class HazardousMaterialUpdate(BaseModel):
    """위험물 수정 요청 스키마."""

    material_name: str | None = None
    cas_number: str | None = None
    item: str | None = None
    ghs_classification: list[str] | None = None
    msds_document: str | None = None
    storage_conditions: str | None = None
    max_storage_qty: Decimal | None = None
    current_qty: Decimal | None = None
    emergency_contact: str | None = None
    regulatory_status: str | None = None


class HazardousMaterial(BaseDocument):
    """위험물 문서."""

    material_name: str = ""
    cas_number: str | None = None
    item: str | None = None
    ghs_classification: list[str] | None = None
    msds_document: str = ""
    storage_conditions: str = ""
    max_storage_qty: Decimal | None = None
    current_qty: Decimal | None = None
    emergency_contact: str = ""
    regulatory_status: str | None = None
