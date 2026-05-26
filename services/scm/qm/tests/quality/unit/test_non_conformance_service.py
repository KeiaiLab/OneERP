"""부적합(NonConformance) 서비스 단위 테스트."""

from __future__ import annotations

import pytest
from oneerp_core.errors import OneERPError
from oneerp_qm_app.quality.services.non_conformance_service import NonConformanceService


class TestNonConformanceService:
    """NonConformanceService 테스트."""

    def test_create_from_inspection(self, mock_collection) -> None:
        """불합격 검사로부터 NC를 생성한다."""
        mock_collection.find_one.return_value = {
            "_id": "QI-2026-00001",
            "item_code": "ITEM-001",
            "result": "rejected",
            "tenant_id": "T1",
        }
        svc = NonConformanceService("T1")
        result = svc.create_from_inspection("QI-2026-00001", severity="major")
        assert result["inspection_id"] == "QI-2026-00001"
        assert result["severity"] == "major"
        assert "nc_id" in result

    def test_create_from_inspection_not_found(self, mock_collection) -> None:
        """존재하지 않는 검사에서 NC 생성 시 에러."""
        mock_collection.find_one.return_value = None
        svc = NonConformanceService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.create_from_inspection("INVALID")

    def test_escalate_minor_to_major(self, mock_collection) -> None:
        """심각도를 minor에서 major로 상향한다."""
        mock_collection.find_one.return_value = {
            "_id": "NC-2026-00001",
            "severity": "minor",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value.modified_count = 1
        svc = NonConformanceService("T1")
        result = svc.escalate("NC-2026-00001", "major")
        assert result["previous"] == "minor"
        assert result["new"] == "major"

    def test_escalate_downgrade_raises(self, mock_collection) -> None:
        """심각도 하향 시 에러."""
        mock_collection.find_one.return_value = {
            "_id": "NC-2026-00001",
            "severity": "critical",
            "tenant_id": "T1",
        }
        svc = NonConformanceService("T1")
        with pytest.raises(OneERPError, match="ERR-QTY-003"):
            svc.escalate("NC-2026-00001", "minor")

    def test_resolve_creates_capa(self, mock_collection) -> None:
        """NC 해결 시 CAPA가 자동 생성된다."""
        mock_collection.find_one.return_value = {
            "_id": "NC-2026-00001",
            "description": "불합격 발생",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value.modified_count = 1
        svc = NonConformanceService("T1")
        result = svc.resolve("NC-2026-00001", "원인 분석 후 재발 방지")
        assert "capa_id" in result
        assert result["nc_id"] == "NC-2026-00001"
