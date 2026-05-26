"""보고서 빌더 서비스 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_analytics_app.services.report_builder_service import ReportBuilderService
from oneerp_core.errors import OneERPError


class TestReportBuilderService:
    """ReportBuilderService 테스트."""

    def test_create_report(self, mock_collection) -> None:
        """보고서를 생성한다."""
        svc = ReportBuilderService("T1")
        result = svc.create_report(
            name="월간 매출",
            report_type="summary",
            data_source="sales_invoices",
            query="SELECT * FROM sales",
        )
        assert result["report_name"] == "월간 매출"
        assert "report_id" in result
        mock_collection.insert_one.assert_called_once()

    def test_execute_report(self, mock_collection) -> None:
        """보고서를 실행한다."""
        mock_collection.find_one.return_value = {
            "_id": "CUSRPT-2026-00001",
            "report_name": "월간 매출",
            "query": "SELECT * FROM sales",
            "tenant_id": "T1",
        }
        svc = ReportBuilderService("T1")
        result = svc.execute_report("CUSRPT-2026-00001", parameters={"month": "3"})
        assert result["report_name"] == "월간 매출"
        assert result["parameters"] == {"month": "3"}

    def test_execute_report_not_found(self, mock_collection) -> None:
        """존재하지 않는 보고서 실행 시 에러."""
        mock_collection.find_one.return_value = None
        svc = ReportBuilderService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.execute_report("INVALID")

    def test_clone_report(self, mock_collection) -> None:
        """보고서를 복제한다."""
        mock_collection.find_one.return_value = {
            "_id": "CUSRPT-2026-00001",
            "report_name": "월간 매출",
            "report_type": "summary",
            "data_source": "sales_invoices",
            "query": "SELECT * FROM sales",
            "is_public": True,
            "tenant_id": "T1",
        }
        svc = ReportBuilderService("T1")
        result = svc.clone_report("CUSRPT-2026-00001", "월간 매출 복사본")
        assert result["report_name"] == "월간 매출 복사본"
        assert result["cloned_from"] == "CUSRPT-2026-00001"

    def test_clone_report_not_found(self, mock_collection) -> None:
        """존재하지 않는 보고서 복제 시 에러."""
        mock_collection.find_one.return_value = None
        svc = ReportBuilderService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.clone_report("INVALID", "복사본")
