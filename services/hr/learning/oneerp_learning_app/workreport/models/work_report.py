"""업무일지(WorkReport) 문서 모델 — WorkReport 모듈.

업무일지 CRUD, 제출, 승인 흐름을 처리하는 핵심 엔티티.

비즈니스 규칙:
- BR-WR-001: 업무일지는 작성자 본인만 수정/삭제 가능
- BR-WR-002: 보고일자는 미래일 수 없음
- BR-WR-003: 업무 항목(items)이 최소 1개 이상이어야 제출 가능
- BR-WR-004: 총 작업시간은 0보다 커야 함
- BR-WR-005: 제출 후에는 수정 불가 (취소 후 재작성)
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel, Field, field_validator


class WorkReportStatus(StrEnum):
    """업무일지 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class WorkReportCategory(StrEnum):
    """업무일지 카테고리."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    PROJECT = "project"


class WorkReportItem(LineItem):
    """업무일지 항목 — 개별 업무 내역.

    BR-WR-004: 작업시간은 0보다 커야 함.
    """

    task_name: str = Field(default="", description="업무명")
    description: str = Field(default="", description="업무 상세 설명")
    project_id: str = Field(default="", description="관련 프로젝트 ID")
    project_name: str = Field(default="", description="관련 프로젝트명")
    hours: Decimal = Field(default=Decimal(0), description="작업 시간(h)")
    progress: int = Field(default=0, description="진행률(%)", ge=0, le=100)
    priority: str = Field(default="normal", description="우선순위")
    remarks: str = Field(default="", description="비고")


class WorkReportCreate(BaseModel):
    """업무일지 생성 요청 스키마.

    BR-WR-002: 보고일자(report_date)는 미래일 불가.
    """

    employee_id: str
    employee_name: str = ""
    department: str = ""
    report_date: date
    category: WorkReportCategory = WorkReportCategory.DAILY
    title: str = ""
    summary: str = ""
    items: list[dict[str, Any]] = Field(default_factory=list)
    next_plan: str = Field(default="", description="차기 업무 계획")
    issues: str = Field(default="", description="이슈/건의사항")
    reviewer_id: str = Field(default="", description="검토자 ID")
    reviewer_name: str = Field(default="", description="검토자명")

    @field_validator("report_date")
    @classmethod
    def _보고일자_미래_불가(cls, v: date) -> date:
        """BR-WR-002: 보고일자는 미래일 수 없다."""
        if v > datetime.now(tz=UTC).date():
            msg = "보고일자는 미래일 수 없습니다 (BR-WR-002)"
            raise ValueError(msg)
        return v


class WorkReportUpdate(BaseModel):
    """업무일지 수정 요청 스키마.

    BR-WR-005: 제출 후에는 수정 불가.
    """

    title: str | None = None
    summary: str | None = None
    items: list[dict[str, Any]] | None = None
    next_plan: str | None = None
    issues: str | None = None
    reviewer_id: str | None = None
    reviewer_name: str | None = None
    category: WorkReportCategory | None = None


class WorkReport(BaseDocument):
    """업무일지 문서 — WorkReport 트랜잭션.

    naming prefix: WR
    """

    employee_id: str = Field(default="", description="작성자 직원 ID")
    employee_name: str = Field(default="", description="작성자명")
    department: str = Field(default="", description="부서")
    report_date: date | None = Field(default=None, description="보고일자")
    category: WorkReportCategory = Field(default=WorkReportCategory.DAILY, description="카테고리")
    title: str = Field(default="", description="제목")
    summary: str = Field(default="", description="요약")
    items: list[dict[str, Any]] = Field(default_factory=list, description="업무 항목 목록")
    total_hours: Decimal = Field(default=Decimal(0), description="총 작업시간(h)")
    next_plan: str = Field(default="", description="차기 업무 계획")
    issues: str = Field(default="", description="이슈/건의사항")
    status: WorkReportStatus = Field(default=WorkReportStatus.DRAFT, description="문서 상태")
    reviewer_id: str = Field(default="", description="검토자 ID")
    reviewer_name: str = Field(default="", description="검토자명")
    reviewed_at: datetime | None = Field(default=None, description="검토일시")
    review_comment: str = Field(default="", description="검토 코멘트")
