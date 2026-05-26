"""업무일지 서비스(WorkReportService) 단위 테스트.

SC-WR-001 ~ SC-WR-010: 핵심 비즈니스 로직 시나리오.
EX-WR-001 ~ EX-WR-005: 예외 시나리오.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 모킹한다."""
    with patch(
        "oneerp_learning_app.workreport.services.work_report_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    """WorkReportService와 모킹된 Repository들을 반환한다."""
    with patch(
        "oneerp_learning_app.workreport.services.work_report_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_learning_app.workreport.services.work_report_service import WorkReportService

        service = WorkReportService(tenant_id="test-tenant")
    return (
        service,
        repos["work_reports"],
        repos["work_report_comments"],
    )


class Test총작업시간계산:
    """SC-WR-001: 총 작업시간 계산."""

    def test_정상_합산(self) -> None:
        """여러 항목의 작업시간이 정확히 합산된다."""
        service, _report_repo, _comment_repo = _make_service()
        items = [
            {"task_name": "설계", "hours": 2.5},
            {"task_name": "구현", "hours": 3.0},
            {"task_name": "리뷰", "hours": 1.5},
        ]
        result = service.calculate_total_hours(items)
        assert result == Decimal("7.0")

    def test_빈_항목(self) -> None:
        """항목이 없으면 0을 반환한다."""
        service, _report_repo, _comment_repo = _make_service()
        result = service.calculate_total_hours([])
        assert result == Decimal(0)


class Test업무일지제출:
    """SC-WR-002: 제출 흐름 검증."""

    def test_정상_제출(self) -> None:
        """SC-WR-002: draft -> submitted 전환."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "draft",
            "items": [{"task_name": "개발", "hours": 4}],
        }

        result = service.submit_report("WR-001", submitted_by="EMP-001")

        assert result["status"] == "submitted"
        assert result["total_hours"] == 4.0
        report_repo.update_by_id.assert_called_once()

    def test_항목없으면_제출불가(self) -> None:
        """EX-WR-001: BR-WR-003 위반."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "draft",
            "items": [],
        }

        with pytest.raises(OneERPError, match="ERR-WR-003"):
            service.submit_report("WR-001", submitted_by="EMP-001")

    def test_작업시간_0이면_제출불가(self) -> None:
        """EX-WR-002: BR-WR-004 위반."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "draft",
            "items": [{"task_name": "회의", "hours": 0}],
        }

        with pytest.raises(OneERPError, match="ERR-WR-004"):
            service.submit_report("WR-001", submitted_by="EMP-001")

    def test_작성자_아닌_사람이_제출_불가(self) -> None:
        """EX-WR-003: BR-WR-001 위반."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "draft",
            "items": [{"task_name": "개발", "hours": 4}],
        }

        with pytest.raises(OneERPError, match="ERR-WR-010"):
            service.submit_report("WR-001", submitted_by="EMP-999")

    def test_이미_제출된_보고서_재제출_불가(self) -> None:
        """EX-WR-004: BR-WR-005 위반."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "submitted",
            "items": [{"task_name": "개발", "hours": 4}],
        }

        with pytest.raises(OneERPError, match="ERR-WR-005"):
            service.submit_report("WR-001", submitted_by="EMP-001")


class Test업무일지승인:
    """SC-WR-003: 승인 흐름 검증."""

    def test_정상_승인(self) -> None:
        """SC-WR-003: submitted -> approved 전환."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "submitted",
            "reviewer_id": "MGR-001",
        }

        result = service.approve_report("WR-001", reviewer_id="MGR-001")

        assert result["status"] == "approved"
        report_repo.update_by_id.assert_called_once()

    def test_이미_승인된_보고서_재승인_불가(self) -> None:
        """EX-WR-005: BR-WR-007 위반."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "status": "approved",
            "reviewer_id": "MGR-001",
        }

        with pytest.raises(OneERPError, match="ERR-WR-007"):
            service.approve_report("WR-001", reviewer_id="MGR-001")

    def test_검토자_불일치시_거부(self) -> None:
        """BR-WR-006: 지정 검토자가 아니면 승인 불가."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "status": "submitted",
            "reviewer_id": "MGR-001",
        }

        with pytest.raises(OneERPError, match="ERR-WR-006"):
            service.approve_report("WR-001", reviewer_id="MGR-999")


class Test업무일지반려:
    """SC-WR-004: 반려 흐름 검증."""

    def test_정상_반려(self) -> None:
        """SC-WR-004: submitted -> rejected 전환."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "status": "submitted",
            "reviewer_id": "MGR-001",
        }

        result = service.reject_report("WR-001", reviewer_id="MGR-001", reason="보완 필요")

        assert result["status"] == "rejected"
        assert result["reason"] == "보완 필요"

    def test_사유_없이_반려_불가(self) -> None:
        """BR-WR-008: 반려 사유 필수."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "status": "submitted",
            "reviewer_id": "MGR-001",
        }

        with pytest.raises(OneERPError, match="ERR-WR-008"):
            service.reject_report("WR-001", reviewer_id="MGR-001", reason="")


class Test업무일지취소:
    """SC-WR-005: 취소 흐름 검증."""

    def test_draft_상태에서_취소(self) -> None:
        """BR-WR-009: draft -> cancelled 전환."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "draft",
        }

        result = service.cancel_report("WR-001", cancelled_by="EMP-001")

        assert result["status"] == "cancelled"

    def test_submitted_상태에서_취소_불가(self) -> None:
        """BR-WR-009: submitted 상태에서는 취소 불가."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "employee_id": "EMP-001",
            "status": "submitted",
        }

        with pytest.raises(OneERPError, match="ERR-WR-009"):
            service.cancel_report("WR-001", cancelled_by="EMP-001")


class Test직원통계:
    """SC-WR-006: 직원 통계 조회."""

    def test_기간별_통계(self) -> None:
        """기간 내 보고서 건수와 총 작업시간을 집계한다."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_many.return_value = [
            {
                "_id": "WR-001",
                "report_date": "2026-03-01",
                "status": "approved",
                "total_hours": 8,
            },
            {
                "_id": "WR-002",
                "report_date": "2026-03-02",
                "status": "submitted",
                "total_hours": 6,
            },
            {
                "_id": "WR-003",
                "report_date": "2026-04-01",
                "status": "approved",
                "total_hours": 7,
            },
        ]

        result = service.get_employee_statistics(
            "EMP-001",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        assert result["total_reports"] == 2
        assert result["approved"] == 1
        assert result["submitted"] == 1
        assert result["total_hours"] == 14.0


class Test템플릿기반생성:
    """SC-WR-007: 템플릿에서 업무일지 생성."""

    def test_템플릿_기반_생성(self) -> None:
        """템플릿 항목이 업무일지에 복사된다."""
        with patch(
            "oneerp_learning_app.workreport.services.work_report_service.Repository"
        ) as mock_repo_cls:
            repos: dict[str, MagicMock] = {}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                repo = MagicMock()
                repos[collection_name] = repo
                return repo

            mock_repo_cls.side_effect = _repo_factory

            from oneerp_learning_app.workreport.services.work_report_service import (
                WorkReportService,
            )

            svc = WorkReportService(tenant_id="test-tenant")

            # create_from_template 내부에서 생성하는 템플릿 리포지토리 모킹
            template_repo = MagicMock()
            template_repo.find_by_id.return_value = {
                "_id": "WRT-001",
                "name": "일일 개발 보고",
                "department": "개발팀",
                "category": "daily",
                "default_items": [
                    {"task_name": "코드 리뷰", "hours": 1},
                    {"task_name": "개발", "hours": 4},
                ],
            }
            mock_repo_cls.side_effect = None
            mock_repo_cls.return_value = template_repo

            result = svc.create_from_template(
                template_id="WRT-001",
                employee_id="EMP-001",
                employee_name="홍길동",
                report_date=date(2026, 3, 15),
            )

        assert result["report_id"] == "WR-001"
        assert result["items_count"] == 2
        repos["work_reports"].insert.assert_called_once()


class Test코멘트추가:
    """SC-WR-008: 코멘트 추가."""

    def test_제출상태에서_코멘트_가능(self) -> None:
        """BR-WR-020: 제출된 업무일지에 코멘트 추가."""
        service, report_repo, comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "status": "submitted",
        }

        result = service.add_comment(
            report_id="WR-001",
            author_id="MGR-001",
            author_name="김매니저",
            content="잘 작성되었습니다",
        )

        assert result["comment_id"] == "WRC-001"
        comment_repo.insert.assert_called_once()

    def test_draft_상태에서_코멘트_불가(self) -> None:
        """BR-WR-020: 초안 상태에서는 코멘트 불가."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "status": "draft",
        }

        with pytest.raises(OneERPError, match="ERR-WR-005"):
            service.add_comment(
                report_id="WR-001",
                author_id="MGR-001",
                author_name="김매니저",
                content="코멘트",
            )

    def test_빈_코멘트_불가(self) -> None:
        """BR-WR-021: 빈 내용 코멘트 불가."""
        service, report_repo, _comment_repo = _make_service()
        report_repo.find_by_id.return_value = {
            "_id": "WR-001",
            "status": "submitted",
        }

        with pytest.raises(OneERPError, match="ERR-WR-008"):
            service.add_comment(
                report_id="WR-001",
                author_id="MGR-001",
                author_name="김매니저",
                content="",
            )
