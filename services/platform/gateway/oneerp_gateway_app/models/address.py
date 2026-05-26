"""주소(Address) 문서 모델.

독립 주소록 컬렉션용 Address(BaseDocument)와
API 요청 스키마를 정의한다.
핵심 필드는 oneerp_core.models.EmbeddedAddress와 공유한다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from oneerp_core.models import EmbeddedAddress
from pydantic import BaseModel


class AddressCreate(EmbeddedAddress):
    """주소 생성 요청 스키마 — EmbeddedAddress 필드를 상속하되 address_title을 필수로 재정의."""

    address_title: str  # 생성 시 필수


class AddressUpdate(BaseModel):
    """주소 수정 요청 스키마."""

    address_title: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    is_primary: bool | None = None


class Address(BaseDocument, EmbeddedAddress):
    """주소 문서 — 독립 컬렉션(addresses)에 저장되는 주소록 엔티티.

    EmbeddedAddress의 필드를 상속하여 일관성을 유지한다.
    """
