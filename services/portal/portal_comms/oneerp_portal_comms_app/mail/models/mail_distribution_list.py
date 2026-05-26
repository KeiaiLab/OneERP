"""메일 배포 목록(MailDistributionList) 문서 모델.

BR-MAIL-040: 배포 목록은 최소 1명 이상의 구성원이 필요하다.
BR-MAIL-041: 배포 목록명은 테넌트 내에서 고유해야 한다.
"""

from __future__ import annotations

from typing import Annotated

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class MailDistributionListCreate(BaseModel):
    """메일 배포 목록 생성 요청 스키마."""

    list_name: Annotated[str, Field(min_length=1, max_length=200)]
    description: str = ""
    members: list[str] = []
    owner_id: str = ""
    is_active: bool = True

    @field_validator("members")
    @classmethod
    def _구성원_최소_하나(cls, v: list[str]) -> list[str]:
        """BR-MAIL-040: 구성원이 최소 1명 이상이어야 한다."""
        if not v:
            msg = "배포 목록에는 최소 1명 이상의 구성원이 필요합니다 [ERR-MAIL-040]"
            raise ValueError(msg)
        return v


class MailDistributionListUpdate(BaseModel):
    """메일 배포 목록 수정 요청 스키마."""

    list_name: str | None = None
    description: str | None = None
    members: list[str] | None = None
    is_active: bool | None = None


class MailDistributionList(BaseDocument):
    """메일 배포 목록 문서.

    BR-MAIL-040 ~ BR-MAIL-041 비즈니스 규칙을 적용한다.
    """

    list_name: str = ""
    description: str = ""
    members: list[str] = []
    owner_id: str = ""
    is_active: bool = True
    member_count: int = 0
