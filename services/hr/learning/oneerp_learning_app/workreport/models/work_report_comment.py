"""업무일지 코멘트(WorkReportComment) 모델 — 검토/피드백 이력 관리.

비즈니스 규칙:
- BR-WR-020: 코멘트는 제출된 업무일지에만 작성 가능
- BR-WR-021: 코멘트 내용(content)은 필수
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WorkReportCommentCreate(BaseModel):
    """업무일지 코멘트 생성 요청 스키마.

    BR-WR-021: 코멘트 내용(content)은 필수.
    """

    work_report_id: str
    content: str
    author_id: str = ""
    author_name: str = ""


class WorkReportCommentUpdate(BaseModel):
    """업무일지 코멘트 수정 요청 스키마."""

    content: str | None = None


class WorkReportComment(BaseDocument):
    """업무일지 코멘트 문서 — 트랜잭션.

    naming prefix: WRC
    """

    work_report_id: str = Field(default="", description="업무일지 ID")
    content: str = Field(default="", description="코멘트 내용")
    author_id: str = Field(default="", description="작성자 ID")
    author_name: str = Field(default="", description="작성자명")
