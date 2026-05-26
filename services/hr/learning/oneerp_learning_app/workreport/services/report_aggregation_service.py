"""업무보고 집계 서비스 — 제출률/피드백/평균 시간/팀 실적.

L2 사양: docs/product/scope/modules/work-report/L2-spec.md (계산 로직 4.1 ~ 4.7)

비즈니스 규칙:
- BR-WRP-020: 제출률 계산 — 0명 부서 처리 (ZeroDivision 방지)

계산 로직:
- 4.1 제출률
- 4.2 피드백 응답률
- 4.3 평균 작성 소요시간
- 4.4 평균 피드백 응답시간
- 4.7 팀 실적 집계

설계 주석:
- Repository I/O는 상위 라우터가 담당. 본 서비스는 pure Python 집계 계산만 수행
- Decimal 기반 퍼센트 계산으로 부동소수점 오차 방지
- 부족 데이터(submitted_at=None 등)는 안전하게 제외
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


class ReportAggregationService:
    """업무보고서 집계 로직."""

    # ------------------------------------------------------------------
    # 4.1 제출률 — BR-WRP-020
    # ------------------------------------------------------------------

    def calculate_submission_rate(
        self,
        *,
        total_expected: int,
        total_submitted: int,
    ) -> Decimal:
        """제출률(%) = total_submitted / total_expected x 100.

        BR-WRP-020: total_expected=0 이면 0.0 반환 (ZeroDivision 방지).
        """
        if total_submitted > total_expected:
            msg = f"제출 건수({total_submitted})가 예상 건수({total_expected})를 초과할 수 없습니다"
            raise ValueError(msg)
        if total_expected == 0:
            return Decimal("0.0")
        rate = (Decimal(total_submitted) / Decimal(total_expected)) * Decimal(100)
        return rate.quantize(Decimal("0.1"))

    # ------------------------------------------------------------------
    # 4.2 피드백 응답률
    # ------------------------------------------------------------------

    def calculate_feedback_rate(
        self,
        *,
        total_submitted: int,
        reports_with_comments: int,
    ) -> Decimal:
        """피드백 응답률(%) = 피드백 있는 보고서 수 / 상신 보고서 수 x 100."""
        if total_submitted == 0:
            return Decimal("0.0")
        rate = (Decimal(reports_with_comments) / Decimal(total_submitted)) * Decimal(100)
        return rate.quantize(Decimal("0.1"))

    # ------------------------------------------------------------------
    # 4.3 평균 작성 소요시간
    # ------------------------------------------------------------------

    def calculate_avg_submission_minutes(
        self,
        reports: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """각 보고서의 submitted_at - created_at 평균(분)을 계산한다."""
        deltas: list[float] = []
        for report in reports:
            created_at = report.get("created_at")
            submitted_at = report.get("submitted_at")
            if not isinstance(created_at, datetime) or not isinstance(submitted_at, datetime):
                continue
            minutes = (submitted_at - created_at).total_seconds() / 60.0
            deltas.append(minutes)

        if not deltas:
            return {"avg_submission_minutes": 0.0, "report_count": 0}
        avg = round(sum(deltas) / len(deltas), 1)
        return {"avg_submission_minutes": avg, "report_count": len(deltas)}

    # ------------------------------------------------------------------
    # 4.4 평균 피드백 응답시간 (first_comment_at - submitted_at)
    # ------------------------------------------------------------------

    def calculate_avg_feedback_minutes(
        self,
        reports: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """상신 시각부터 첫 댓글 시각까지의 평균(분)을 계산한다.

        각 report 에 'submitted_at', 'first_comment_at' 필드가 있어야 한다.
        """
        deltas: list[float] = []
        for report in reports:
            submitted_at = report.get("submitted_at")
            first_comment_at = report.get("first_comment_at")
            if not isinstance(submitted_at, datetime) or not isinstance(first_comment_at, datetime):
                continue
            minutes = (first_comment_at - submitted_at).total_seconds() / 60.0
            deltas.append(minutes)

        if not deltas:
            return {"avg_feedback_minutes": 0.0, "report_count": 0}
        avg = round(sum(deltas) / len(deltas), 1)
        return {"avg_feedback_minutes": avg, "report_count": len(deltas)}

    # ------------------------------------------------------------------
    # 4.7 팀 실적 집계
    # ------------------------------------------------------------------

    def aggregate_team_performance(
        self,
        *,
        department_id: str,
        period_start: date,
        period_end: date,
        reports: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """부서별 보고서의 수치 섹션과 프로젝트 스냅샷을 집계한다.

        수식:
        - section_summary: 동일 section_key 기준 SUM(numeric_value)
        - total_tasks_completed: 프로젝트 스냅샷의 tasks_completed 합
        - total_tasks_in_progress: 프로젝트 스냅샷의 tasks_in_progress 합
        """
        section_totals: dict[str, dict[str, Any]] = {}
        total_completed = 0
        total_in_progress = 0

        for report in reports:
            for section in report.get("sections", []) or []:
                numeric_value = section.get("numeric_value")
                if numeric_value is None:
                    continue
                key = section.get("section_key", "")
                title = section.get("section_title", "")
                entry = section_totals.setdefault(
                    key,
                    {"key": key, "title": title, "total_value": 0.0},
                )
                entry["total_value"] += float(numeric_value)

            for snapshot in report.get("project_snapshots", []) or []:
                total_completed += int(snapshot.get("tasks_completed", 0) or 0)
                total_in_progress += int(snapshot.get("tasks_in_progress", 0) or 0)

        return {
            "department_id": department_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "report_count": len(reports),
            "section_summaries": list(section_totals.values()),
            "total_tasks_completed": total_completed,
            "total_tasks_in_progress": total_in_progress,
        }
