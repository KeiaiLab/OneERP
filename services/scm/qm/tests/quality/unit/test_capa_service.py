"""CAPA 서비스 단위 테스트."""

from __future__ import annotations

from datetime import date

import pytest
from oneerp_core.errors import OneERPError
from oneerp_qm_app.quality.services.capa_service import CAPAService


class TestCAPAService:
    """CAPAService 테스트."""

    def test_create_capa_from_nc(self, mock_collection) -> None:
        """NC로부터 CAPA를 생성한다."""
        mock_collection.find_one.return_value = {
            "_id": "NC-2026-00001",
            "description": "불합격 발생",
            "tenant_id": "T1",
        }
        svc = CAPAService("T1")
        result = svc.create_capa_from_nc(
            nc_id="NC-2026-00001",
            capa_type="corrective",
            corrective_action="재검사 실시",
            responsible="홍길동",
            due_date=date(2026, 4, 30),
        )
        assert result["nc_id"] == "NC-2026-00001"
        assert result["capa_type"] == "corrective"
        assert "capa_id" in result
        mock_collection.insert_one.assert_called_once()

    def test_create_capa_from_nc_not_found(self, mock_collection) -> None:
        """존재하지 않는 NC에서 CAPA 생성 시 에러."""
        mock_collection.find_one.return_value = None
        svc = CAPAService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.create_capa_from_nc("INVALID", "corrective", "조치", "담당자", date(2026, 4, 30))

    def test_close_capa(self, mock_collection) -> None:
        """조치가 기입된 CAPA를 마감한다."""
        mock_collection.find_one.return_value = {
            "_id": "CAPA-2026-00001",
            "corrective_action": "재검사 실시",
            "is_closed": False,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value.modified_count = 1
        svc = CAPAService("T1")
        result = svc.close_capa("CAPA-2026-00001", effectiveness_verified=True)
        assert result["is_closed"] is True

    def test_close_capa_without_action_raises(self, mock_collection) -> None:
        """조치 미기입 시 마감 에러."""
        mock_collection.find_one.return_value = {
            "_id": "CAPA-2026-00001",
            "corrective_action": "",
            "is_closed": False,
            "tenant_id": "T1",
        }
        svc = CAPAService("T1")
        with pytest.raises(OneERPError, match="ERR-QTY-001"):
            svc.close_capa("CAPA-2026-00001")

    def test_get_overdue_capas(self, mock_collection) -> None:
        """기한 초과 CAPA 목록을 조회한다."""
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {"_id": "CAPA-2026-00001", "due_date": date(2026, 1, 1)},
        ]
        svc = CAPAService("T1")
        result = svc.get_overdue_capas(as_of_date=date(2026, 3, 1))
        assert len(result) == 1

    def test_get_capa_statistics(self, mock_collection) -> None:
        """CAPA 통계를 반환한다."""
        mock_collection.count_documents.side_effect = [10, 4, 6, 2]
        svc = CAPAService("T1")
        stats = svc.get_capa_statistics()
        assert stats["total"] == 10
        assert stats["open"] == 4
        assert stats["closed"] == 6
        assert stats["overdue"] == 2
