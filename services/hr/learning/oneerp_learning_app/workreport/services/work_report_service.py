"""업무일지 서비스 — 제출/승인/반려/통계 비즈니스 로직.

비즈니스 규칙:
- BR-WR-001: 작성자 본인만 수정/삭제 가능
- BR-WR-003: 항목이 최소 1개 이상이어야 제출 가능
- BR-WR-004: 총 작업시간이 0보다 커야 함
- BR-WR-005: 제출 후에는 수정 불가
- BR-WR-006: 승인/반려는 검토자만 가능
- BR-WR-007: 이미 승인된 보고서는 재승인 불가
- BR-WR-008: 반려 시 사유 필수
- BR-WR-009: 취소는 draft/rejected 상태에서만 가능

에러 코드:
- ERR-WR-001: 업무일지를 찾을 수 없음
- ERR-WR-002: 보고일자 미래일 오류
- ERR-WR-003: 업무 항목 없음
- ERR-WR-004: 총 작업시간 0 이하
- ERR-WR-005: 제출 후 수정 불가
- ERR-WR-006: 검토자 권한 없음
- ERR-WR-007: 이미 승인된 보고서
- ERR-WR-008: 반려 사유 미기재
- ERR-WR-009: 취소 불가 상태
- ERR-WR-010: 작성자 불일치
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_learning_app.workreport.models.work_report import (
    WorkReport,
    WorkReportItem,
    WorkReportStatus,
)

logger = logging.getLogger(__name__)


class WorkReportService:
    """업무일지 비즈니스 로직.

    업무일지 제출, 승인/반려, 통계 조회를 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._report_repo = Repository("work_reports", tenant_id=tenant_id)
        self._comment_repo = Repository("work_report_comments", tenant_id=tenant_id)

    def _find_report_or_raise(self, report_id: str) -> dict[str, Any]:
        """업무일지를 조회하거나 ERR-WR-001 에러를 발생한다."""
        doc = self._report_repo.find_by_id(report_id)
        if not doc:
            raise OneERPError(
                status_code=404,
                error="ERR-WR-001",
                detail=f"업무일지 '{report_id}'를 찾을 수 없습니다",
            )
        return doc

    def calculate_total_hours(self, items: list[dict[str, Any]]) -> Decimal:
        """업무 항목들의 총 작업시간을 계산한다.

        BR-WR-004: 총 작업시간은 0보다 커야 함.
        """
        total = Decimal(0)
        for item in items:
            hours = item.get("hours", 0)
            total += Decimal(str(hours))
        return total

    def validate_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """업무 항목을 검증하고 WorkReportItem으로 변환한다.

        BR-WR-003: 항목이 최소 1개 이상이어야 함.
        """
        if not items:
            raise OneERPError(
                status_code=400,
                error="ERR-WR-003",
                detail="업무 항목이 최소 1개 이상이어야 합니다 (BR-WR-003)",
            )
        validated: list[dict[str, Any]] = []
        for idx, item_data in enumerate(items):
            item = WorkReportItem(idx=idx + 1, **item_data)
            validated.append(item.model_dump())
        return validated

    def submit_report(self, report_id: str, submitted_by: str) -> dict[str, Any]:
        """업무일지를 제출한다.

        BR-WR-001: 작성자 본인만 제출 가능.
        BR-WR-003: 항목이 최소 1개 이상이어야 제출 가능.
        BR-WR-004: 총 작업시간이 0보다 커야 함.
        BR-WR-005: 이미 제출된 보고서는 재제출 불가.

        Args:
            report_id: 업무일지 ID.
            submitted_by: 제출자 ID.

        Returns:
            제출 결과 딕셔너리.

        Raises:
            OneERPError: 비즈니스 규칙 위반 시.
        """
        doc = self._find_report_or_raise(report_id)

        # BR-WR-001: 작성자 본인 확인
        if doc.get("employee_id", "") != submitted_by:
            raise OneERPError(
                status_code=403,
                error="ERR-WR-010",
                detail="작성자 본인만 제출할 수 있습니다 (BR-WR-001)",
            )

        # BR-WR-005: 이미 제출된 보고서 확인
        current_status = doc.get("status", WorkReportStatus.DRAFT)
        if current_status not in (WorkReportStatus.DRAFT, WorkReportStatus.REJECTED):
            raise OneERPError(
                status_code=400,
                error="ERR-WR-005",
                detail=f"현재 상태({current_status})에서는 제출할 수 없습니다 (BR-WR-005)",
            )

        items = doc.get("items", [])

        # BR-WR-003: 항목 최소 1개
        if not items:
            raise OneERPError(
                status_code=400,
                error="ERR-WR-003",
                detail="업무 항목이 최소 1개 이상이어야 합니다 (BR-WR-003)",
            )

        # BR-WR-004: 총 작업시간 > 0
        total_hours = self.calculate_total_hours(items)
        if total_hours <= 0:
            raise OneERPError(
                status_code=400,
                error="ERR-WR-004",
                detail="총 작업시간이 0보다 커야 합니다 (BR-WR-004)",
            )

        self._report_repo.update_by_id(
            report_id,
            {
                "status": WorkReportStatus.SUBMITTED,
                "total_hours": float(total_hours),
                "updated_at": datetime.now(tz=UTC),
            },
        )

        logger.info(
            "업무일지 제출: %s (작성자: %s, 총시간: %s)",
            report_id,
            submitted_by,
            total_hours,
        )

        return {
            "report_id": report_id,
            "status": WorkReportStatus.SUBMITTED,
            "total_hours": float(total_hours),
        }

    def approve_report(
        self,
        report_id: str,
        reviewer_id: str,
        comment: str = "",
    ) -> dict[str, Any]:
        """업무일지를 승인한다.

        BR-WR-006: 검토자만 승인 가능.
        BR-WR-007: 이미 승인된 보고서는 재승인 불가.

        Args:
            report_id: 업무일지 ID.
            reviewer_id: 검토자 ID.
            comment: 승인 코멘트.

        Returns:
            승인 결과 딕셔너리.
        """
        doc = self._find_report_or_raise(report_id)

        # BR-WR-007: 이미 승인된 보고서
        current_status = doc.get("status", "")
        if current_status == WorkReportStatus.APPROVED:
            raise OneERPError(
                status_code=400,
                error="ERR-WR-007",
                detail="이미 승인된 업무일지입니다 (BR-WR-007)",
            )

        # submitted 상태만 승인 가능
        if current_status != WorkReportStatus.SUBMITTED:
            raise OneERPError(
                status_code=400,
                error="ERR-WR-005",
                detail=f"제출 상태에서만 승인 가능합니다 (현재: {current_status})",
            )

        # BR-WR-006: 검토자 확인
        assigned_reviewer = doc.get("reviewer_id", "")
        if assigned_reviewer and assigned_reviewer != reviewer_id:
            raise OneERPError(
                status_code=403,
                error="ERR-WR-006",
                detail="지정된 검토자만 승인할 수 있습니다 (BR-WR-006)",
            )

        now = datetime.now(tz=UTC)
        self._report_repo.update_by_id(
            report_id,
            {
                "status": WorkReportStatus.APPROVED,
                "reviewer_id": reviewer_id,
                "reviewed_at": now,
                "review_comment": comment,
                "updated_at": now,
            },
        )

        logger.info("업무일지 승인: %s (검토자: %s)", report_id, reviewer_id)

        return {
            "report_id": report_id,
            "status": WorkReportStatus.APPROVED,
            "reviewer_id": reviewer_id,
            "reviewed_at": now.isoformat(),
        }

    def reject_report(
        self,
        report_id: str,
        reviewer_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """업무일지를 반려한다.

        BR-WR-006: 검토자만 반려 가능.
        BR-WR-008: 반려 사유 필수.

        Args:
            report_id: 업무일지 ID.
            reviewer_id: 검토자 ID.
            reason: 반려 사유.

        Returns:
            반려 결과 딕셔너리.
        """
        doc = self._find_report_or_raise(report_id)

        # BR-WR-008: 반려 사유 필수
        if not reason or not reason.strip():
            raise OneERPError(
                status_code=400,
                error="ERR-WR-008",
                detail="반려 사유를 입력해야 합니다 (BR-WR-008)",
            )

        current_status = doc.get("status", "")
        if current_status != WorkReportStatus.SUBMITTED:
            raise OneERPError(
                status_code=400,
                error="ERR-WR-005",
                detail=f"제출 상태에서만 반려 가능합니다 (현재: {current_status})",
            )

        # BR-WR-006: 검토자 확인
        assigned_reviewer = doc.get("reviewer_id", "")
        if assigned_reviewer and assigned_reviewer != reviewer_id:
            raise OneERPError(
                status_code=403,
                error="ERR-WR-006",
                detail="지정된 검토자만 반려할 수 있습니다 (BR-WR-006)",
            )

        now = datetime.now(tz=UTC)
        self._report_repo.update_by_id(
            report_id,
            {
                "status": WorkReportStatus.REJECTED,
                "reviewer_id": reviewer_id,
                "reviewed_at": now,
                "review_comment": reason,
                "updated_at": now,
            },
        )

        logger.info("업무일지 반려: %s (검토자: %s, 사유: %s)", report_id, reviewer_id, reason)

        return {
            "report_id": report_id,
            "status": WorkReportStatus.REJECTED,
            "reviewer_id": reviewer_id,
            "reason": reason,
        }

    def cancel_report(self, report_id: str, cancelled_by: str) -> dict[str, Any]:
        """업무일지를 취소한다.

        BR-WR-009: draft 또는 rejected 상태에서만 취소 가능.
        BR-WR-001: 작성자 본인만 취소 가능.

        Args:
            report_id: 업무일지 ID.
            cancelled_by: 취소 요청자 ID.

        Returns:
            취소 결과 딕셔너리.
        """
        doc = self._find_report_or_raise(report_id)

        # BR-WR-001: 작성자 본인 확인
        if doc.get("employee_id", "") != cancelled_by:
            raise OneERPError(
                status_code=403,
                error="ERR-WR-010",
                detail="작성자 본인만 취소할 수 있습니다 (BR-WR-001)",
            )

        # BR-WR-009: 취소 가능 상태 확인
        current_status = doc.get("status", "")
        if current_status not in (WorkReportStatus.DRAFT, WorkReportStatus.REJECTED):
            raise OneERPError(
                status_code=400,
                error="ERR-WR-009",
                detail=f"현재 상태({current_status})에서는 취소할 수 없습니다 (BR-WR-009)",
            )

        self._report_repo.update_by_id(
            report_id,
            {
                "status": WorkReportStatus.CANCELLED,
                "updated_at": datetime.now(tz=UTC),
            },
        )

        logger.info("업무일지 취소: %s (요청자: %s)", report_id, cancelled_by)

        return {
            "report_id": report_id,
            "status": WorkReportStatus.CANCELLED,
        }

    def get_employee_statistics(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """직원의 업무일지 통계를 조회한다.

        기간 내 제출/승인/반려 건수, 총 작업시간을 반환한다.

        Args:
            employee_id: 직원 ID.
            start_date: 시작일.
            end_date: 종료일.

        Returns:
            통계 결과 딕셔너리.
        """
        reports = self._report_repo.find_many(
            {"employee_id": employee_id},
            limit=10000,
        )

        # 기간 필터링
        filtered: list[dict[str, Any]] = []
        for r in reports:
            rd = r.get("report_date")
            if rd is None:
                continue
            if isinstance(rd, str):
                rd = date.fromisoformat(rd)
            elif isinstance(rd, datetime):
                rd = rd.date()
            if start_date <= rd <= end_date:
                filtered.append(r)

        total_reports = len(filtered)
        submitted = sum(1 for r in filtered if r.get("status") == WorkReportStatus.SUBMITTED)
        approved = sum(1 for r in filtered if r.get("status") == WorkReportStatus.APPROVED)
        rejected = sum(1 for r in filtered if r.get("status") == WorkReportStatus.REJECTED)

        total_hours = Decimal(0)
        for r in filtered:
            h = r.get("total_hours", 0)
            total_hours += Decimal(str(h))

        return {
            "employee_id": employee_id,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_reports": total_reports,
            "submitted": submitted,
            "approved": approved,
            "rejected": rejected,
            "total_hours": float(total_hours),
        }

    def create_from_template(
        self,
        template_id: str,
        employee_id: str,
        employee_name: str,
        report_date: date,
    ) -> dict[str, Any]:
        """템플릿에서 업무일지를 생성한다.

        BR-WR-011: 템플릿 항목을 기본 항목으로 복사.

        Args:
            template_id: 템플릿 ID.
            employee_id: 작성자 ID.
            employee_name: 작성자명.
            report_date: 보고일자.

        Returns:
            생성 결과 딕셔너리.
        """
        template_repo = Repository("work_report_templates", tenant_id=self._tenant_id)
        template = template_repo.find_by_id(template_id)
        if not template:
            raise OneERPError(
                status_code=404,
                error="ERR-WR-001",
                detail=f"템플릿 '{template_id}'을 찾을 수 없습니다",
            )

        report_id = generate_name("WR", tenant_id=self._tenant_id)
        items = template.get("default_items", [])

        doc = WorkReport(
            _id=report_id,
            employee_id=employee_id,
            employee_name=employee_name,
            department=template.get("department", ""),
            report_date=report_date,
            category=template.get("category", "daily"),
            title=f"{template.get('name', '')} - {report_date.isoformat()}",
            items=items,
            tenant_id=self._tenant_id,
        )
        self._report_repo.insert(doc)

        logger.info(
            "템플릿 기반 업무일지 생성: %s (템플릿: %s, 작성자: %s)",
            report_id,
            template_id,
            employee_id,
        )

        return {
            "report_id": report_id,
            "template_id": template_id,
            "items_count": len(items),
        }

    def add_comment(
        self,
        report_id: str,
        author_id: str,
        author_name: str,
        content: str,
    ) -> dict[str, Any]:
        """업무일지에 코멘트를 추가한다.

        BR-WR-020: 제출된 업무일지에만 코멘트 가능.
        BR-WR-021: 코멘트 내용은 필수.

        Args:
            report_id: 업무일지 ID.
            author_id: 작성자 ID.
            author_name: 작성자명.
            content: 코멘트 내용.

        Returns:
            코멘트 생성 결과.
        """
        doc = self._find_report_or_raise(report_id)

        # BR-WR-020: 제출 이후 상태만 코멘트 가능
        current_status = doc.get("status", "")
        if current_status not in (
            WorkReportStatus.SUBMITTED,
            WorkReportStatus.APPROVED,
            WorkReportStatus.REJECTED,
        ):
            raise OneERPError(
                status_code=400,
                error="ERR-WR-005",
                detail="제출된 업무일지에만 코멘트를 작성할 수 있습니다 (BR-WR-020)",
            )

        # BR-WR-021: 코멘트 내용 필수
        if not content or not content.strip():
            raise OneERPError(
                status_code=400,
                error="ERR-WR-008",
                detail="코멘트 내용을 입력해야 합니다 (BR-WR-021)",
            )

        from oneerp_learning_app.workreport.models.work_report_comment import WorkReportComment

        comment_id = generate_name("WRC", tenant_id=self._tenant_id)
        comment_doc = WorkReportComment(
            _id=comment_id,
            work_report_id=report_id,
            content=content.strip(),
            author_id=author_id,
            author_name=author_name,
            tenant_id=self._tenant_id,
        )
        self._comment_repo.insert(comment_doc)

        logger.info("업무일지 코멘트 추가: %s → %s", comment_id, report_id)

        return {
            "comment_id": comment_id,
            "work_report_id": report_id,
            "author_id": author_id,
        }
