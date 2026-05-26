"""업무일지 모델 단위 테스트 — Pydantic 검증."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from oneerp_learning_app.workreport.models.work_report import (
    WorkReport,
    WorkReportCategory,
    WorkReportCreate,
    WorkReportItem,
    WorkReportStatus,
)


def _today():
    """UTC 기준 오늘 날짜를 반환한다."""
    return datetime.now(tz=UTC).date()


class TestWorkReportModel:
    """WorkReport 모델 검증."""

    def test_기본값_확인(self) -> None:
        """모든 필드의 기본값이 올바른지 확인."""
        report = WorkReport()
        assert report.status == WorkReportStatus.DRAFT
        assert report.category == WorkReportCategory.DAILY
        assert report.total_hours == Decimal(0)
        assert report.items == []

    def test_카테고리_enum(self) -> None:
        """카테고리 StrEnum 값 확인."""
        assert WorkReportCategory.DAILY == "daily"
        assert WorkReportCategory.WEEKLY == "weekly"
        assert WorkReportCategory.MONTHLY == "monthly"
        assert WorkReportCategory.PROJECT == "project"

    def test_상태_enum(self) -> None:
        """상태 StrEnum 값 확인."""
        assert WorkReportStatus.DRAFT == "draft"
        assert WorkReportStatus.SUBMITTED == "submitted"
        assert WorkReportStatus.APPROVED == "approved"
        assert WorkReportStatus.REJECTED == "rejected"
        assert WorkReportStatus.CANCELLED == "cancelled"


class TestWorkReportCreate:
    """WorkReportCreate 스키마 검증."""

    def test_정상_생성(self) -> None:
        """올바른 데이터로 생성 스키마 검증."""
        create = WorkReportCreate(
            employee_id="EMP-001",
            employee_name="홍길동",
            report_date=_today(),
            title="일일 업무보고",
        )
        assert create.employee_id == "EMP-001"
        assert create.category == WorkReportCategory.DAILY

    def test_미래일자_거부(self) -> None:
        """BR-WR-002: 미래 보고일자 거부."""
        future_date = _today() + timedelta(days=1)
        with pytest.raises(ValueError, match="BR-WR-002"):
            WorkReportCreate(
                employee_id="EMP-001",
                report_date=future_date,
            )

    def test_오늘_일자_허용(self) -> None:
        """오늘 날짜는 허용된다."""
        today = _today()
        create = WorkReportCreate(
            employee_id="EMP-001",
            report_date=today,
        )
        assert create.report_date == today


class TestWorkReportItem:
    """WorkReportItem 모델 검증."""

    def test_진행률_범위(self) -> None:
        """progress는 0~100 사이만 허용."""
        item = WorkReportItem(task_name="개발", hours=Decimal(4), progress=50)
        assert item.progress == 50

    def test_진행률_초과_거부(self) -> None:
        """progress가 100을 초과하면 거부."""
        with pytest.raises(ValueError, match="less than or equal to 100"):
            WorkReportItem(task_name="개발", hours=Decimal(4), progress=101)

    def test_진행률_음수_거부(self) -> None:
        """progress가 0 미만이면 거부."""
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            WorkReportItem(task_name="개발", hours=Decimal(4), progress=-1)
