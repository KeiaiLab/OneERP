"""위험물(HazardousMaterial) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class HazardousMaterialCreate(BaseModel):
    """위험물 생성 요청 스키마."""

    item_code: str
    un_number: str = ""
    hazard_class: str = ""
    packing_group: str = ""
    handling_instructions: str = ""


class HazardousMaterialUpdate(BaseModel):
    """위험물 수정 요청 스키마."""

    item_code: str | None = None
    un_number: str | None = None
    hazard_class: str | None = None
    packing_group: str | None = None
    handling_instructions: str | None = None


class HazardousMaterial(BaseDocument):
    """위험물 문서."""

    item_code: str = ""
    un_number: str = ""
    hazard_class: str = ""
    packing_group: str = ""
    handling_instructions: str = ""
