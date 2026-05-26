"""운송사(Carrier) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CarrierCreate(BaseModel):
    """운송사 생성 요청 스키마."""

    carrier_name: str
    contact_person: str = ""
    phone: str = ""
    is_active: bool = True


class CarrierUpdate(BaseModel):
    """운송사 수정 요청 스키마."""

    carrier_name: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class Carrier(BaseDocument):
    """운송사 문서."""

    carrier_name: str = ""
    contact_person: str = ""
    phone: str = ""
    is_active: bool = True
