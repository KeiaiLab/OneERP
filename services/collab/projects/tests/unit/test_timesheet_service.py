"""타임시트 서비스(TimesheetService) 단위 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_projects_app.services.timesheet_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_projects_app.services.timesheet_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_projects_app.services.timesheet_service import TimesheetService

        service = TimesheetService(tenant_id="test-tenant")
    return (
        service,
        repos["timesheets"],
        repos["project_billings"],
        repos["tasks"],
        repos["activity_types"],
    )


class Test타임시트제출:
    def test_정상_제출(self) -> None:
        service, ts_repo, _billing, task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = {
            "_id": "TS-001",
            "total_hours": 40.0,
            "docstatus": 0,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "time_logs": [
                {
                    "date": "2026-03-03",
                    "project_ref": "PROJ-001",
                    "task_ref": "TASK-001",
                    "hours": 32.0,
                    "activity_type": "개발",
                },
                {
                    "date": "2026-03-04",
                    "project_ref": "PROJ-001",
                    "task_ref": "TASK-001",
                    "hours": 8.0,
                    "activity_type": "회의",
                },
            ],
        }
        task_repo.find_by_id.return_value = {"_id": "TASK-001", "actual_time": 2.0}

        result = service.submit_timesheet("TS-001")

        assert result["status"] == "submitted"
        assert result["total_hours"] == Decimal("40.0")
        event_data = ts_repo.submit_with_event.call_args.kwargs["event_data"]
        assert event_data["payroll_ready_hours"] == 40.0
        assert event_data["activity_hours"] == [
            {"activity_type": "개발", "hours": 32.0},
            {"activity_type": "회의", "hours": 8.0},
        ]
        task_repo.update_by_id.assert_called_once_with("TASK-001", {"actual_time": Decimal("42.0")})

    def test_0시간_에러(self) -> None:
        service, ts_repo, _billing, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = {
            "_id": "TS-001",
            "total_hours": 0,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
        }

        with pytest.raises(OneERPError, match="ERR-PRJ-008"):
            service.submit_timesheet("TS-001")

    def test_time_logs_합계와_total_hours_불일치_에러(self) -> None:
        service, ts_repo, _billing, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = {
            "_id": "TS-001",
            "total_hours": 8.0,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "time_logs": [
                {"date": "2026-03-03", "task_ref": "TASK-001", "hours": 4.0},
                {"date": "2026-03-04", "task_ref": "TASK-002", "hours": 2.0},
            ],
        }

        with pytest.raises(OneERPError, match="ERR-PRJ-009"):
            service.submit_timesheet("TS-001")

    def test_time_logs_작업일자_누락_에러(self) -> None:
        service, ts_repo, _billing, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = {
            "_id": "TS-001",
            "total_hours": 8.0,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "time_logs": [{"task_ref": "TASK-001", "hours": 8.0, "activity_type": "개발"}],
        }

        with pytest.raises(OneERPError, match="ERR-PRJ-018"):
            service.submit_timesheet("TS-001")

    def test_time_logs_작업일자_기간밖_에러(self) -> None:
        service, ts_repo, _billing, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = {
            "_id": "TS-001",
            "total_hours": 8.0,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "time_logs": [
                {
                    "date": "2026-03-07",
                    "task_ref": "TASK-001",
                    "hours": 8.0,
                    "activity_type": "개발",
                }
            ],
        }

        with pytest.raises(OneERPError, match="ERR-PRJ-019"):
            service.submit_timesheet("TS-001")

    def test_타임시트_미존재(self) -> None:
        service, ts_repo, _billing, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.submit_timesheet("TS-999")


class Test타임시트청구:
    def test_정상_인보이스(self) -> None:
        service, ts_repo, billing_repo, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = {
            "_id": "TS-001",
            "employee_id": "EMP-001",
            "total_hours": 160.0,
        }

        result = service.generate_invoice_from_timesheet("TS-001", hourly_rate=Decimal(50_000))

        assert result["billing_id"] == "PBL-001"
        assert result["amount"] == Decimal(8000000)  # 160 * 50,000
        billing_repo.insert.assert_called_once()
        ts_repo.update_by_id.assert_called_with("TS-001", {"billed": True})

    def test_타임시트_미존재(self) -> None:
        service, ts_repo, _billing, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.generate_invoice_from_timesheet("TS-999", Decimal(50_000))

    def test_활동유형_청구단가를_자동적용한다(self) -> None:
        service, ts_repo, billing_repo, _task_repo, activity_type_repo = _make_service()
        ts_repo.find_by_id.return_value = {
            "_id": "TS-001",
            "employee_id": "EMP-001",
            "total_hours": 10.0,
            "time_logs": [
                {"date": "2026-03-03", "activity_type": "개발", "hours": 6.0},
                {"date": "2026-03-04", "activity_type": "설계", "hours": 4.0},
            ],
        }
        activity_type_repo.find_many.side_effect = [
            [{"activity_type": "개발", "billing_rate": Decimal(120000), "is_active": True}],
            [{"activity_type": "설계", "billing_rate": Decimal(80000), "is_active": True}],
        ]

        result = service.generate_invoice_from_timesheet("TS-001")

        assert result["amount"] == Decimal(1040000)
        inserted = billing_repo.insert.call_args.args[0]
        assert inserted["rate_source"] == "activity_type"
        assert inserted["line_items"] == [
            {
                "activity_type": "개발",
                "hours": Decimal("6.0"),
                "rate": Decimal(120000),
                "amount": Decimal(720000),
            },
            {
                "activity_type": "설계",
                "hours": Decimal("4.0"),
                "rate": Decimal(80000),
                "amount": Decimal(320000),
            },
        ]


class Test일괄인보이싱:
    def test_미청구_일괄_처리(self) -> None:
        service, ts_repo, billing_repo, _task_repo, _activity_type_repo = _make_service()
        ts_repo.find_many.return_value = [
            {"_id": "TS-001", "employee_id": "EMP-001", "total_hours": 80},
            {"_id": "TS-002", "employee_id": "EMP-002", "total_hours": 120},
        ]
        ts_repo.find_by_id.side_effect = lambda tid: {
            "TS-001": {"_id": "TS-001", "employee_id": "EMP-001", "total_hours": 80},
            "TS-002": {"_id": "TS-002", "employee_id": "EMP-002", "total_hours": 120},
        }[tid]

        results = service.auto_invoice_timesheets("2026-03", hourly_rate=Decimal(50_000))

        assert len(results) == 2
        assert billing_repo.insert.call_count == 2
