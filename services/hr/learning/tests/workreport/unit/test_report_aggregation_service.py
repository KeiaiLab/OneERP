"""업무보고 집계 서비스(ReportAggregationService) 단위 테스트.

대상 비즈니스 룰:
- BR-WRP-020: 제출률 계산 (ZeroDivision 방지)
- 계산 로직 4.1: 제출률
- 계산 로직 4.2: 피드백 응답률
- 계산 로직 4.3: 평균 작성 소요시간
- 계산 로직 4.7: 팀 실적 집계
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from oneerp_learning_app.workreport.services.report_aggregation_service import (
    ReportAggregationService,
)


class Test제출률_계산:
    """BR-WRP-020 및 계산 로직 4.1."""

    def test_정상_제출률(self) -> None:
        service = ReportAggregationService()
        result = service.calculate_submission_rate(
            total_expected=100,
            total_submitted=85,
        )
        assert result == Decimal("85.0")

    def test_전원_제출(self) -> None:
        service = ReportAggregationService()
        assert service.calculate_submission_rate(
            total_expected=20,
            total_submitted=20,
        ) == Decimal("100.0")

    def test_대상자_0명_ZeroDivision_방지(self) -> None:
        """BR-WRP-020: total_expected=0 이면 0.0."""
        service = ReportAggregationService()
        assert service.calculate_submission_rate(
            total_expected=0,
            total_submitted=0,
        ) == Decimal("0.0")

    def test_제출_초과_오류(self) -> None:
        service = ReportAggregationService()
        with pytest.raises(ValueError, match="초과"):
            service.calculate_submission_rate(
                total_expected=10,
                total_submitted=15,
            )


class Test피드백응답률_계산:
    """계산 로직 4.2."""

    def test_정상_응답률(self) -> None:
        service = ReportAggregationService()
        result = service.calculate_feedback_rate(
            total_submitted=50,
            reports_with_comments=35,
        )
        assert result == Decimal("70.0")

    def test_상신_0건_ZeroDivision(self) -> None:
        service = ReportAggregationService()
        assert service.calculate_feedback_rate(
            total_submitted=0,
            reports_with_comments=0,
        ) == Decimal("0.0")


class Test평균_작성_소요시간:
    """계산 로직 4.3."""

    def test_평균_작성시간_분단위(self) -> None:
        service = ReportAggregationService()
        # 3건의 보고서 (2.5시간, 1시간, 3시간) → 평균 (150+60+180)/3 = 130분
        reports = [
            {
                "created_at": datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                "submitted_at": datetime(2026, 4, 1, 11, 30, tzinfo=UTC),
            },
            {
                "created_at": datetime(2026, 4, 2, 10, 0, tzinfo=UTC),
                "submitted_at": datetime(2026, 4, 2, 11, 0, tzinfo=UTC),
            },
            {
                "created_at": datetime(2026, 4, 3, 14, 0, tzinfo=UTC),
                "submitted_at": datetime(2026, 4, 3, 17, 0, tzinfo=UTC),
            },
        ]
        result = service.calculate_avg_submission_minutes(reports)
        assert result["avg_submission_minutes"] == 130.0
        assert result["report_count"] == 3

    def test_보고서_없음(self) -> None:
        service = ReportAggregationService()
        result = service.calculate_avg_submission_minutes([])
        assert result["avg_submission_minutes"] == 0.0
        assert result["report_count"] == 0

    def test_submitted_at_없는_보고서는_제외(self) -> None:
        service = ReportAggregationService()
        reports = [
            {
                "created_at": datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                "submitted_at": None,
            },
            {
                "created_at": datetime(2026, 4, 2, 9, 0, tzinfo=UTC),
                "submitted_at": datetime(2026, 4, 2, 10, 0, tzinfo=UTC),
            },
        ]
        result = service.calculate_avg_submission_minutes(reports)
        assert result["report_count"] == 1
        assert result["avg_submission_minutes"] == 60.0


class Test팀실적_집계:
    """계산 로직 4.7: 부서별 실적 집계."""

    def test_수치_섹션_SUM_집계(self) -> None:
        service = ReportAggregationService()
        reports = [
            {
                "author_id": "EMP-001",
                "sections": [
                    {
                        "section_key": "sales_amount",
                        "section_title": "매출액",
                        "numeric_value": 1000.0,
                    },
                    {
                        "section_key": "calls",
                        "section_title": "고객 콜 수",
                        "numeric_value": 20,
                    },
                ],
                "project_snapshots": [
                    {"tasks_completed": 3, "tasks_in_progress": 2},
                ],
            },
            {
                "author_id": "EMP-002",
                "sections": [
                    {
                        "section_key": "sales_amount",
                        "section_title": "매출액",
                        "numeric_value": 1500.0,
                    },
                    {
                        "section_key": "calls",
                        "section_title": "고객 콜 수",
                        "numeric_value": 15,
                    },
                ],
                "project_snapshots": [
                    {"tasks_completed": 5, "tasks_in_progress": 1},
                ],
            },
        ]
        result = service.aggregate_team_performance(
            department_id="DEPT-01",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
            reports=reports,
        )
        # 섹션 요약: sales_amount=2500, calls=35
        summaries = {s["key"]: s for s in result["section_summaries"]}
        assert summaries["sales_amount"]["total_value"] == 2500.0
        assert summaries["calls"]["total_value"] == 35.0
        # 프로젝트 합산: completed=8, in_progress=3
        assert result["total_tasks_completed"] == 8
        assert result["total_tasks_in_progress"] == 3
        assert result["report_count"] == 2

    def test_빈_보고서_집계(self) -> None:
        service = ReportAggregationService()
        result = service.aggregate_team_performance(
            department_id="DEPT-01",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
            reports=[],
        )
        assert result["report_count"] == 0
        assert result["section_summaries"] == []
        assert result["total_tasks_completed"] == 0

    def test_수치가_없는_섹션_무시(self) -> None:
        service = ReportAggregationService()
        reports = [
            {
                "sections": [
                    {
                        "section_key": "today_work",
                        "section_title": "금일 업무",
                        "content": "개발 진행",
                    },
                    {
                        "section_key": "tasks_done",
                        "section_title": "완료 작업 수",
                        "numeric_value": 10,
                    },
                ],
            }
        ]
        result = service.aggregate_team_performance(
            department_id="DEPT-01",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
            reports=reports,
        )
        keys = [s["key"] for s in result["section_summaries"]]
        assert "today_work" not in keys
        assert "tasks_done" in keys
