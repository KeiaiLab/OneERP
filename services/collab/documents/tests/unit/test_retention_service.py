"""보존 정책 서비스 단위 테스트.

BR-DOC-003: 보존 정책 자동 적용.
UT-DOC-003, UT-DOC-004: 보존 만료일 계산 테스트.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from oneerp_documents_app.services.retention_service import RetentionService


class TestRetentionService:
    """RetentionService 테스트."""

    def test_보존만료일_계산_5년(self, mock_collection: MagicMock) -> None:
        """UT-DOC-003: 5년 보존 시 만료일을 올바르게 계산한다."""
        mock_collection.find_one.return_value = {
            "_id": "RP-0001",
            "retention_years": 5,
            "retention_months": 0,
            "tenant_id": "T1",
        }

        svc = RetentionService("T1")
        base = datetime(2026, 3, 28, tzinfo=UTC)
        result = svc.calculate_retention_until("RP-0001", base)

        assert result is not None
        assert result.year == 2031
        assert result.month == 3
        assert result.day == 28

    def test_보존만료일_계산_복합기간(self, mock_collection: MagicMock) -> None:
        """3년 6개월 보존 기간 계산."""
        mock_collection.find_one.return_value = {
            "_id": "RP-0002",
            "retention_years": 3,
            "retention_months": 6,
            "tenant_id": "T1",
        }

        svc = RetentionService("T1")
        base = datetime(2026, 12, 31, tzinfo=UTC)
        result = svc.calculate_retention_until("RP-0002", base)

        assert result is not None
        assert result.year == 2030
        assert result.month == 6
        assert result.day == 30

    def test_보존만료일_계산_윤년(self, mock_collection: MagicMock) -> None:
        """UT-DOC-004: 윤년 2/29 기준 1년 후 = 2/28."""
        mock_collection.find_one.return_value = {
            "_id": "RP-0003",
            "retention_years": 1,
            "retention_months": 0,
            "tenant_id": "T1",
        }

        svc = RetentionService("T1")
        base = datetime(2024, 2, 29, tzinfo=UTC)
        result = svc.calculate_retention_until("RP-0003", base)

        assert result is not None
        assert result.year == 2025
        assert result.month == 2
        assert result.day == 28

    def test_정책_미존재시_None(self, mock_collection: MagicMock) -> None:
        """존재하지 않는 정책 ID 시 None 반환."""
        mock_collection.find_one.return_value = None

        svc = RetentionService("T1")
        result = svc.calculate_retention_until("RP-INVALID")

        assert result is None

    def test_보존기간_확인_True(self, mock_collection: MagicMock) -> None:
        """보존 기간 내인 문서는 True를 반환한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "retention_until": datetime(2030, 1, 1, tzinfo=UTC),
            "tenant_id": "T1",
        }

        svc = RetentionService("T1")
        assert svc.is_under_retention("DOC-0001") is True

    def test_보존기간_확인_False_만료(self, mock_collection: MagicMock) -> None:
        """보존 기간이 만료된 문서는 False를 반환한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "retention_until": datetime(2020, 1, 1, tzinfo=UTC),
            "tenant_id": "T1",
        }

        svc = RetentionService("T1")
        assert svc.is_under_retention("DOC-0001") is False

    def test_보존기간_확인_False_미설정(self, mock_collection: MagicMock) -> None:
        """보존 정책이 미설정된 문서는 False를 반환한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "retention_until": None,
            "tenant_id": "T1",
        }

        svc = RetentionService("T1")
        assert svc.is_under_retention("DOC-0001") is False
