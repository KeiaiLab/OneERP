"""포털 사용자(PortalUser) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class PortalUserStatus(StrEnum):
    """포털 사용자 상태."""

    ACTIVE = "active"
    DISABLED = "disabled"


class PortalUserCreate(BaseModel):
    """포털 사용자 생성 요청 스키마."""

    user_name: str
    email: str = ""
    portal_type: str = ""
    linked_entity_id: str = ""
    is_active: bool = True


class PortalUserUpdate(BaseModel):
    """포털 사용자 수정 요청 스키마."""

    user_name: str | None = None
    email: str | None = None
    portal_type: str | None = None
    linked_entity_id: str | None = None
    is_active: bool | None = None


class PortalUser(BaseDocument):
    """포털 사용자 문서."""

    status: PortalUserStatus = Field(
        default=PortalUserStatus.ACTIVE,
        description="포털 사용자 상태",
    )
    user_name: str = ""
    email: str = ""
    portal_type: str = ""
    linked_entity_id: str = ""
    is_active: bool = True
