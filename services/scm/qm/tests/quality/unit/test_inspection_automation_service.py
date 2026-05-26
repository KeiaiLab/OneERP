"""검사 자동화 서비스 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_core.errors import OneERPError
from oneerp_qm_app.quality.services.inspection_automation_service import InspectionAutomationService


class TestInspectionAutomationService:
    """InspectionAutomationService 테스트."""

    def test_trigger_incoming_inspection(self, mock_collection) -> None:
        """입고 검사를 자동 생성한다."""
        svc = InspectionAutomationService("T1")
        result = svc.trigger_incoming_inspection("PR-2026-00001", "ITEM-001")
        assert result["inspection_type"] == "incoming"
        assert "inspection_id" in result
        mock_collection.insert_one.assert_called_once()

    def test_trigger_in_process_inspection(self, mock_collection) -> None:
        """공정 중 검사를 자동 생성한다."""
        svc = InspectionAutomationService("T1")
        result = svc.trigger_in_process_inspection("SE-2026-00001", "ITEM-002")
        assert result["inspection_type"] == "in_process"
        assert "inspection_id" in result

    def test_auto_create_nc_on_failure_rejected(self, mock_collection) -> None:
        """불합격 검사에 대해 NC를 자동 생성한다."""
        mock_collection.find_one.return_value = {
            "_id": "QI-2026-00001",
            "item_code": "ITEM-001",
            "result": "rejected",
            "tenant_id": "T1",
        }
        svc = InspectionAutomationService("T1")
        result = svc.auto_create_nc_on_failure("QI-2026-00001")
        assert result is not None
        assert "nc_id" in result

    def test_auto_create_nc_on_failure_accepted(self, mock_collection) -> None:
        """합격 검사는 NC를 생성하지 않는다."""
        mock_collection.find_one.return_value = {
            "_id": "QI-2026-00001",
            "item_code": "ITEM-001",
            "result": "accepted",
            "tenant_id": "T1",
        }
        svc = InspectionAutomationService("T1")
        result = svc.auto_create_nc_on_failure("QI-2026-00001")
        assert result is None

    def test_auto_create_nc_not_found(self, mock_collection) -> None:
        """존재하지 않는 검사에서 NC 생성 시 에러."""
        mock_collection.find_one.return_value = None
        svc = InspectionAutomationService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.auto_create_nc_on_failure("INVALID")
