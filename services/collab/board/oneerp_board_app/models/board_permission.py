"""게시판 권한(BoardPermission) 문서 모델.

엔티티 정의: L2-spec 1.7
권한 수준: read < write < manage
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class GranteeType(StrEnum):
    """권한 대상 유형."""

    USER = "user"
    DEPARTMENT = "department"
    GROUP = "group"
    ROLE = "role"
    ALL = "all"


class PermissionLevel(StrEnum):
    """권한 수준."""

    READ = "read"
    WRITE = "write"
    MANAGE = "manage"


class BoardPermissionCreate(BaseModel):
    """게시판 권한 생성 요청 스키마."""

    board_id: str
    grantee_type: GranteeType
    grantee_id: str | None = None
    permission: PermissionLevel
    is_active: bool = True
    granted_by: str = ""


class BoardPermissionUpdate(BaseModel):
    """게시판 권한 수정 요청 스키마."""

    permission: PermissionLevel | None = None
    is_active: bool | None = None


class BoardPermission(BaseDocument):
    """게시판 권한 문서.

    권한 계층: read(1) < write(2) < manage(3).
    사용자의 최대 권한 수준을 반환한다.
    """

    board_id: str = ""
    grantee_type: GranteeType = GranteeType.ALL
    grantee_id: str | None = None
    permission: PermissionLevel = PermissionLevel.READ
    is_active: bool = True
    granted_by: str = ""
