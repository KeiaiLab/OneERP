"""초대자(Invitee) 문서 모델.

BR-CAL-020: 초대자는 이벤트에 소속되어야 한다.
BR-CAL-021: 동일 이벤트에 동일 사용자 중복 초대 불가.
BR-CAL-022: 응답 상태: pending → accepted/declined/tentative.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class InviteeResponseStatus(StrEnum):
    """초대 응답 상태."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class InviteeCreate(BaseModel):
    """초대자 생성 요청 스키마."""

    event_id: str
    user_id: str
    user_name: str = ""
    email: str = ""
    is_required: bool = True


class InviteeUpdate(BaseModel):
    """초대자 수정 요청 스키마."""

    response_status: InviteeResponseStatus | None = None
    response_comment: str | None = None


class Invitee(BaseDocument):
    """초대자 문서.

    naming prefix: CINV
    BR-CAL-020: 초대자는 이벤트에 소속되어야 한다.
    BR-CAL-022: 응답 상태: pending → accepted/declined/tentative.
    """

    event_id: str = Field(default="", description="이벤트 ID")
    user_id: str = Field(default="", description="사용자 ID")
    user_name: str = Field(default="", description="사용자 이름")
    email: str = Field(default="", description="이메일")
    is_required: bool = Field(default=True, description="필수 참석 여부")
    response_status: InviteeResponseStatus = Field(
        default=InviteeResponseStatus.PENDING,
        description="응답 상태",
    )
    response_comment: str = Field(default="", description="응답 코멘트")
