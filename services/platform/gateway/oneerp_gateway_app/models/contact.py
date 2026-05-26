"""연락처(Contact) 문서 모델.

독립 연락처 컬렉션용 Contact(BaseDocument)와
API 요청 스키마를 정의한다.
핵심 필드는 oneerp_core.models.EmbeddedContact와 공유한다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from oneerp_core.models import EmbeddedContact
from pydantic import BaseModel


class ContactCreate(EmbeddedContact):
    """연락처 생성 요청 스키마 — EmbeddedContact 필드를 상속하되 contact_name을 필수로 재정의."""

    contact_name: str  # 생성 시 필수


class ContactUpdate(BaseModel):
    """연락처 수정 요청 스키마."""

    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    designation: str | None = None
    is_primary: bool | None = None


class Contact(BaseDocument, EmbeddedContact):
    """연락처 문서 — 독립 컬렉션(contacts)에 저장되는 연락처 엔티티.

    EmbeddedContact의 필드를 상속하여 일관성을 유지한다.
    """
