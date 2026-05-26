"""면접 피드백(InterviewFeedback) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class InterviewFeedbackCreate(BaseModel):
    """면접 피드백 생성 요청 스키마."""

    interview_round_id: str
    interviewer: str = ""
    rating: int = 0
    feedback: str = ""
    recommendation: str = ""


class InterviewFeedbackUpdate(BaseModel):
    """면접 피드백 수정 요청 스키마."""

    interview_round_id: str | None = None
    interviewer: str | None = None
    rating: int | None = None
    feedback: str | None = None
    recommendation: str | None = None


class InterviewFeedback(BaseDocument):
    """면접 피드백 문서."""

    interview_round_id: str = ""
    interviewer: str = ""
    rating: int = 0
    feedback: str = ""
    recommendation: str = ""
